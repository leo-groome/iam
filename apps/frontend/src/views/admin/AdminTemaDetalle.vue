<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { computed, onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';
import { mediaService } from '@/services/media.service';

type ExamOption = {
  texto: string;
  is_correct: boolean;
};

type ExamQuestion = {
  id?: string;
  enunciado: string;
  options: ExamOption[];
};

const route = useRoute();
const router = useRouter();
const courseId = route.params.id as string;
const modId = route.params.modId as string;
const temaId = route.params.temaId as string;

const isNew = temaId === 'nuevo';
const curso = ref<any>(null);
const mod = ref<any>(null);
const tema = ref<any>(null);
const loading = ref(false);
const saving = ref(false);
const isUploading = ref(false);
const uploadPhase = ref<'optimizing' | 'uploading' | 'done' | null>(null);

const errorMessage = ref('');
const successMessage = ref('');
const title = ref('');
const contentType = ref('video');
const hasExam = ref(false);
const contentBody = ref('');
const durationMinutes = ref<number | null>(null);
const examMinScore = ref(70);
const mediaKey = ref('');
const questions = ref<ExamQuestion[]>([]);

const makeEmptyQuestion = (): ExamQuestion => ({
  enunciado: '',
  options: [
    { texto: '', is_correct: true },
    { texto: '', is_correct: false },
    { texto: '', is_correct: false },
  ],
});

const normalizeQuestion = (q: any): ExamQuestion => {
  const options = (q.options ?? []).map((o: any) => ({
    texto: o.texto ?? '',
    is_correct: Boolean(o.is_correct),
  }));
  if (!options.some((o: ExamOption) => o.is_correct) && options[0]) {
    options[0].is_correct = true;
  }
  return {
    id: q.id,
    enunciado: q.enunciado ?? '',
    options: options.length >= 3 ? options : makeEmptyQuestion().options,
  };
};

const canEditQuestions = computed(() => !isNew);

onMounted(async () => {
  loading.value = true;
  try {
    curso.value = await adminService.getCourse(courseId);
    mod.value = curso.value?.modules?.find((m: any) => m.id === modId) ?? null;
    if (!isNew) {
      tema.value = await adminService.getTopicDetail(temaId);
      if (tema.value) {
        title.value = tema.value.title;
        contentType.value = tema.value.content_type;
        hasExam.value = tema.value.has_exam;
        contentBody.value = tema.value.content_body || '';
        durationMinutes.value = tema.value.duration_seconds ? Math.round(tema.value.duration_seconds / 60) : null;
        examMinScore.value = tema.value.exam_min_score || 70;
        mediaKey.value = tema.value.media_key || '';
        questions.value = (tema.value.questions ?? []).map(normalizeQuestion);
      }
    }
  } catch (err) {
    errorMessage.value = 'No se pudo cargar el tema.';
    console.error('Error loading topic:', err);
  } finally {
    loading.value = false;
  }
});

const setCorrectOption = (questionIndex: number, optionIndex: number) => {
  questions.value[questionIndex].options = questions.value[questionIndex].options.map((option, idx) => ({
    ...option,
    is_correct: idx === optionIndex,
  }));
};

const addQuestion = () => {
  questions.value.push(makeEmptyQuestion());
};

const removeQuestion = (index: number) => {
  questions.value.splice(index, 1);
};

const moveQuestion = (index: number, direction: -1 | 1) => {
  const nextIndex = index + direction;
  if (nextIndex < 0 || nextIndex >= questions.value.length) return;
  const [question] = questions.value.splice(index, 1);
  questions.value.splice(nextIndex, 0, question);
};

const addOption = (questionIndex: number) => {
  const question = questions.value[questionIndex];
  if (question.options.length >= 5) return;
  question.options.push({ texto: '', is_correct: false });
};

const removeOption = (questionIndex: number, optionIndex: number) => {
  const question = questions.value[questionIndex];
  if (question.options.length <= 3) return;
  const wasCorrect = question.options[optionIndex].is_correct;
  question.options.splice(optionIndex, 1);
  if (wasCorrect && question.options[0]) {
    setCorrectOption(questionIndex, 0);
  }
};

const validateQuestions = (): string | null => {
  if (!hasExam.value) return null;
  for (const [qIndex, question] of questions.value.entries()) {
    if (question.enunciado.trim().length < 5) return `La pregunta ${qIndex + 1} necesita al menos 5 caracteres.`;
    if (question.options.length < 3 || question.options.length > 5) return `La pregunta ${qIndex + 1} debe tener entre 3 y 5 opciones.`;
    if (question.options.some((option) => option.texto.trim().length < 1)) return `Todas las opciones de la pregunta ${qIndex + 1} deben tener texto.`;
    if (question.options.filter((option) => option.is_correct).length !== 1) return `La pregunta ${qIndex + 1} debe tener una respuesta correcta.`;
  }
  return null;
};

const buildQuestionPayload = () => questions.value.map((question, questionIndex) => ({
  enunciado: question.enunciado.trim(),
  order_index: questionIndex,
  options: question.options.map((option, optionIndex) => ({
    texto: option.texto.trim(),
    is_correct: option.is_correct,
    order_index: optionIndex,
  })),
}));

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  let scope: 'video' | 'pdf' | 'imagen' = 'imagen';
  if (contentType.value === 'video') scope = 'video';
  else if (contentType.value === 'pdf') scope = 'pdf';

  isUploading.value = true;
  uploadPhase.value = null;
  errorMessage.value = '';
  try {
    const key = await mediaService.uploadFile(file, scope, (phase) => {
      uploadPhase.value = phase;
    });
    mediaKey.value = key;
  } catch (err: any) {
    console.error('Error uploading file:', err);
    errorMessage.value = 'No se pudo subir el archivo: ' + err.message;
  } finally {
    isUploading.value = false;
    uploadPhase.value = null;
  }
};

const handleSave = async () => {
  errorMessage.value = '';
  successMessage.value = '';
  const validationError = validateQuestions();
  if (validationError) {
    errorMessage.value = validationError;
    return;
  }

  saving.value = true;
  try {
    const dur = durationMinutes.value !== null && durationMinutes.value !== undefined ? Number(durationMinutes.value) * 60 : null;
    const score = Number(examMinScore.value) || 70;
    const formData: any = {
      title: title.value,
      content_type: contentType.value,
      has_exam: hasExam.value,
      content_body: contentBody.value || null,
      duration_seconds: dur,
      exam_min_score: score,
      media_key: mediaKey.value || null,
    };
    if (isNew) {
      const created = await adminService.createTopic(modId, formData);
      router.replace(`/admin/cursos/${courseId}/modulos/${modId}/temas/${created.id}`);
      return;
    }
    await adminService.updateTopic(temaId, formData);
    await adminService.replaceTopicQuestions(temaId, hasExam.value ? buildQuestionPayload() : []);
    successMessage.value = 'Tema y examen guardados.';
  } catch (err) {
    errorMessage.value = 'No se pudo guardar el tema.';
    console.error('Error saving topic:', err);
  } finally {
    saving.value = false;
  }
};
</script>

<template>
  <div class="page-container">
    <div class="mb-4 text-sm text-[var(--color-text-muted)] flex items-center gap-2">
      <router-link to="/admin/cursos" class="hover:text-[var(--color-primary)] transition-colors">Cursos</router-link>
      <span>/</span>
      <router-link :to="`/admin/cursos/${courseId}`" class="hover:text-[var(--color-primary)] transition-colors">{{ curso?.title || 'Curso' }}</router-link>
      <span>/</span>
      <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}`" class="hover:text-[var(--color-primary)] transition-colors">{{ mod?.title || 'Módulo' }}</router-link>
      <span v-if="!isNew">/</span>
      <span v-if="!isNew" class="font-medium text-[var(--color-text)]">{{ title || tema?.title }}</span>
    </div>

    <header class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">{{ isNew ? "Nuevo tema" : `Editar: ${tema?.title || title}` }}</h1>
      <button @click="handleSave" :disabled="saving || loading" class="btn btn-primary">{{ saving ? 'Guardando...' : 'Guardar' }}</button>
    </header>

    <div v-if="errorMessage" class="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{{ errorMessage }}</div>
    <div v-if="successMessage" class="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{{ successMessage }}</div>

    <div class="grid lg:grid-cols-3 gap-6">
      <div class="card p-6 lg:col-span-2 space-y-4">
        <div>
          <label class="label">Título</label>
          <input class="input" minlength="3" maxlength="60" v-model="title" />
        </div>
        <div>
          <label class="label">Tipo de contenido</label>
          <select class="input" v-model="contentType">
            <option value="video">Video</option>
            <option value="pdf">PDF</option>
            <option value="imagen">Imagen / Infografía</option>
            <option value="texto">Texto enriquecido</option>
          </select>
        </div>

        <div v-if="contentType === 'texto'">
          <label class="label">Contenido</label>
          <textarea
            class="input min-h-60 font-mono text-sm"
            v-model="contentBody"
            maxlength="20000"
            placeholder="Escribe el contenido aquí (Markdown soportado)"
          />
          <p class="text-xs text-[var(--color-text-muted)] mt-1">{{ contentBody.length }} / 20000 caracteres</p>
        </div>

        <div v-if="contentType === 'video'">
          <label class="label">Duración (minutos)</label>
          <input
            type="number"
            class="input"
            v-model.number="durationMinutes"
            min="1"
            max="300"
            placeholder="Ej: 15"
          />
        </div>

        <div v-if="contentType !== 'texto'">
          <label class="label">Archivo Multimedia</label>
          <div v-if="mediaKey" class="border border-[var(--color-border)] rounded-xl p-4 flex items-center justify-between bg-[var(--color-bg-hover)] mb-4">
            <div class="flex items-center gap-3 overflow-hidden">
              <svg class="w-8 h-8 text-[var(--color-primary)] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
              <span class="text-sm font-medium truncate">{{ mediaKey.split('/').pop() || 'Archivo actual' }}</span>
            </div>
            <button type="button" @click="mediaKey = ''" class="text-xs text-red-600 hover:bg-red-50 px-2.5 py-1 rounded font-medium border border-red-200">Reemplazar</button>
          </div>
          <div v-else-if="isUploading" class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-8 text-center bg-[var(--color-app-bg)] flex flex-col items-center">
            <svg class="animate-spin h-6 w-6 text-[var(--color-primary)] mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <p class="text-sm font-medium text-[var(--color-text)]">{{ uploadPhase === 'optimizing' ? 'Optimizando video para streaming...' : 'Subiendo a Cloudflare R2...' }}</p>
            <p class="text-xs text-[var(--color-text-muted)] mt-1">
              {{ uploadPhase === 'optimizing' ? 'Reordenando metadatos (sin recodificar)' : 'Transfiriendo directamente al CDN' }}
            </p>
          </div>
          <div v-else class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-6 text-center hover:bg-[var(--color-app-bg)] transition-colors relative cursor-pointer group">
            <input type="file" :accept="contentType === 'video' ? 'video/mp4, video/webm' : (contentType === 'pdf' ? 'application/pdf' : 'image/jpeg, image/png, image/webp')" @change="handleFileUpload" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
            <div class="space-y-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p class="text-sm text-[var(--color-text-muted)]">Arrastra o haz clic para subir</p>
              <p class="text-xs text-[var(--color-text-muted)]">
                {{ contentType === 'video' ? 'Video (mp4/webm, máx 500 MB)' : (contentType === 'pdf' ? 'Documento PDF (máx 50 MB)' : 'Imagen (jpeg/png/webp, máx 10 MB)') }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="card p-6">
          <h3 class="font-semibold mb-3">Examen</h3>
          <label class="flex items-center justify-between text-sm">
            <span>Requiere cuestionario</span>
            <input type="checkbox" v-model="hasExam" />
          </label>

          <div v-if="hasExam" class="mt-4 space-y-4">
            <div>
              <label class="label">Puntaje mínimo para aprobar: {{ examMinScore }}%</label>
              <input type="range" class="w-full" v-model.number="examMinScore" min="50" max="100" />
              <div class="flex justify-between text-xs text-[var(--color-text-muted)] mt-1">
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>
            <p v-if="!canEditQuestions" class="text-sm text-[var(--color-text-muted)]">
              Guarda el tema nuevo para habilitar el banco de preguntas.
            </p>
          </div>
        </div>
      </div>
    </div>

    <section v-if="hasExam && canEditQuestions" class="mt-6 space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold">Banco de preguntas</h2>
          <p class="text-sm text-[var(--color-text-muted)]">{{ questions.length }} preguntas configuradas</p>
        </div>
        <button type="button" @click="addQuestion" class="btn btn-secondary">+ Agregar pregunta</button>
      </div>

      <div v-if="questions.length === 0" class="card p-8 text-center text-[var(--color-text-muted)]">
        No hay preguntas todavía.
      </div>

      <div v-for="(question, questionIndex) in questions" :key="question.id ?? questionIndex" class="card p-5 space-y-4">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1">
            <label class="label">Pregunta {{ questionIndex + 1 }}</label>
            <textarea class="input min-h-24" maxlength="300" v-model="question.enunciado" placeholder="Escribe la pregunta"></textarea>
            <p class="help">5-300 caracteres.</p>
          </div>
          <div class="flex gap-2 shrink-0">
            <button type="button" @click="moveQuestion(questionIndex, -1)" :disabled="questionIndex === 0" class="btn btn-secondary px-3">Subir</button>
            <button type="button" @click="moveQuestion(questionIndex, 1)" :disabled="questionIndex === questions.length - 1" class="btn btn-secondary px-3">Bajar</button>
            <button type="button" @click="removeQuestion(questionIndex)" class="btn btn-secondary text-[var(--color-error)]">Eliminar</button>
          </div>
        </div>

        <div>
          <label class="label">Opciones de respuesta</label>
          <div class="space-y-2">
            <div v-for="(option, optionIndex) in question.options" :key="optionIndex" class="flex items-center gap-3">
              <input
                type="radio"
                :name="`correct-${questionIndex}`"
                :checked="option.is_correct"
                @change="setCorrectOption(questionIndex, optionIndex)"
                class="w-5 h-5 accent-[var(--color-primary)]"
              />
              <input class="input flex-1" maxlength="150" v-model="option.texto" :placeholder="`Opción ${optionIndex + 1}`" />
              <button type="button" @click="removeOption(questionIndex, optionIndex)" :disabled="question.options.length <= 3" class="text-[var(--color-text-muted)] hover:text-[var(--color-error)] disabled:opacity-40">x</button>
            </div>
          </div>
          <button type="button" @click="addOption(questionIndex)" :disabled="question.options.length >= 5" class="btn btn-ghost mt-3 text-sm">+ Agregar opción</button>
        </div>
      </div>
    </section>
  </div>
</template>
