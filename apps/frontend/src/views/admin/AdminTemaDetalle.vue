<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { computed, onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';
import type { ContentBlockIn } from '@/services/admin.service';
import AdminContentBlocks from '@/components/ui/AdminContentBlocks.vue';
import type { Block } from '@/components/ui/AdminContentBlocks.vue';

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

const errorMessage = ref('');
const successMessage = ref('');
const title = ref('');
const hasExam = ref(false);
const examMinScore = ref(70);
const questions = ref<ExamQuestion[]>([]);

const makeEmptyBlock = (): Block => ({
  kind: 'video',
  media_key: null,
  content_body: null,
  duration_seconds: null,
  order_index: 0,
});

const blocks = ref<Block[]>([makeEmptyBlock()]);

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

const normalizeBlock = (b: any, index: number): Block => ({
  id: b.id,
  kind: b.kind,
  media_key: b.media_key ?? null,
  content_body: b.content_body ?? null,
  duration_seconds: b.duration_seconds ?? null,
  order_index: b.order_index ?? index,
});

onMounted(async () => {
  loading.value = true;
  try {
    curso.value = await adminService.getCourse(courseId);
    mod.value = curso.value?.modules?.find((m: any) => m.id === modId) ?? null;
    if (!isNew) {
      tema.value = await adminService.getTopicDetail(temaId);
      if (tema.value) {
        title.value = tema.value.title;
        hasExam.value = tema.value.has_exam;
        examMinScore.value = tema.value.exam_min_score || 70;
        questions.value = (tema.value.questions ?? []).map(normalizeQuestion);
        const loadedBlocks: any[] = tema.value.blocks ?? [];
        blocks.value = loadedBlocks.length > 0
          ? [...loadedBlocks]
              .sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0))
              .map((b, i) => normalizeBlock(b, i))
          : [makeEmptyBlock()];
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

const validateBlocks = (): string | null => {
  if (blocks.value.length === 0) return 'Agrega al menos un bloque de contenido.';
  for (const [index, block] of blocks.value.entries()) {
    if (block.kind === 'texto') {
      if (!block.content_body || !block.content_body.trim()) {
        return `El bloque ${index + 1} (texto) necesita contenido.`;
      }
    } else if (!block.media_key) {
      return `El bloque ${index + 1} (${block.kind}) necesita un archivo.`;
    }
  }
  return null;
};

const buildBlockPayload = (): ContentBlockIn[] =>
  blocks.value.map((block, index) => ({
    kind: block.kind,
    media_key: block.kind === 'texto' ? null : block.media_key,
    content_body: block.kind === 'texto' ? block.content_body : null,
    duration_seconds: block.duration_seconds ?? null,
    order_index: index,
  }));

const handleSave = async () => {
  errorMessage.value = '';
  successMessage.value = '';
  const validationError = validateQuestions();
  if (validationError) {
    errorMessage.value = validationError;
    return;
  }
  const blocksError = validateBlocks();
  if (blocksError) {
    errorMessage.value = blocksError;
    return;
  }

  saving.value = true;
  try {
    const score = Number(examMinScore.value) || 70;
    const formData: any = {
      title: title.value,
      has_exam: hasExam.value,
      exam_min_score: score,
    };
    let topicId = temaId;
    if (isNew) {
      // The backend still requires content_type on creation; derive it from
      // the first block so the topic row is created in a valid state before
      // the block list (source of truth) is synced right after.
      const created = await adminService.createTopic(modId, {
        ...formData,
        content_type: blocks.value[0].kind,
      });
      topicId = created.id;
      await adminService.replaceTopicBlocks(topicId, buildBlockPayload());
      router.replace(`/admin/cursos/${courseId}/modulos/${modId}/temas/${topicId}`);
      return;
    }
    await adminService.updateTopic(topicId, formData);
    await adminService.replaceTopicBlocks(topicId, buildBlockPayload());
    await adminService.replaceTopicQuestions(topicId, hasExam.value ? buildQuestionPayload() : []);
    successMessage.value = 'Tema y examen guardados.';
  } catch (err) {
    errorMessage.value = 'No se pudo guardar el tema.';
    console.error('Error saving topic:', err);
  } finally {
    saving.value = false;
  }
};

const handleDeleteTopic = async () => {
  if (!confirm('¿Eliminar esta clase permanentemente? Esta acción no se puede deshacer.')) return;
  try {
    await adminService.deleteTopic(temaId);
    router.push(`/admin/cursos/${courseId}/modulos/${modId}`);
  } catch (err: any) {
    errorMessage.value = 'No se pudo eliminar la clase.';
    console.error('Error deleting topic:', err);
    alert('Error al eliminar clase: ' + (err.message || 'Error desconocido'));
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
      <div class="flex gap-2">
        <button v-if="!isNew" @click="handleDeleteTopic" class="btn border border-red-200 text-red-600 hover:bg-red-50">Eliminar clase</button>
        <button @click="handleSave" :disabled="saving || loading" class="btn btn-primary">{{ saving ? 'Guardando...' : 'Guardar' }}</button>
      </div>
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
          <label class="label">Bloques de contenido</label>
          <AdminContentBlocks v-model="blocks" />
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
