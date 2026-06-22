<script setup lang="ts">
import { useRoute } from 'vue-router';
import { onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';

const route = useRoute();
const courseId = route.params.id as string;
const modId = route.params.modId as string;
const temaId = route.params.temaId as string;

const isNew = temaId === 'nuevo';
const curso = ref(null);
const mod = ref(null);
const tema = ref(null);
const loading = ref(false);
const title = ref('');
const contentType = ref('video');
const hasExam = ref(false);
const contentBody = ref('');
const durationMinutes = ref(null);
const examMinScore = ref(70);

onMounted(async () => {
  loading.value = true;
  try {
    curso.value = await adminService.getCourse(courseId);
    mod.value = curso.value?.modules?.find((m: any) => m.id === modId) ?? null;
    if (!isNew) {
      tema.value = mod.value?.topics?.find((t: any) => t.id === temaId) ?? null;
      if (tema.value) {
        title.value = tema.value.title;
        contentType.value = tema.value.content_type;
        hasExam.value = tema.value.has_exam;
        contentBody.value = tema.value.content_body || '';
        durationMinutes.value = tema.value.duration_seconds ? Math.round(tema.value.duration_seconds / 60) : null;
        examMinScore.value = tema.value.exam_min_score || 70;
      }
    }
  } catch (err) {
    console.error('Error loading course:', err);
  } finally {
    loading.value = false;
  }
});

const handleSave = async () => {
  try {
    const dur = durationMinutes.value !== null && durationMinutes.value !== '' ? Number(durationMinutes.value) * 60 : null;
    const score = Number(examMinScore.value) || 70;
    const formData: any = {
      title: title.value,
      content_type: contentType.value,
      has_exam: hasExam.value,
      content_body: contentBody.value || null,
      duration_seconds: dur,
      exam_min_score: score,
    };
    if (isNew) {
      await adminService.createTopic(modId, formData);
    } else {
      await adminService.updateTopic(temaId, formData);
    }
  } catch (err) {
    console.error('Error saving topic:', err);
  }
};
</script>

<template>
  <div class="page-container">


  <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Módulo</router-link>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Nuevo tema" : `Editar: ${tema?.title}` }}</h1>
    <button @click="handleSave" class="btn btn-primary">Guardar</button>
  </header>

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

      <div>
        <label class="label">Subir archivo</label>
        <div class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-8 text-center text-sm text-[var(--color-text-muted)]">
          Arrastra video (mp4/webm, máx 500 MB) o PDF (máx 50 MB).
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
            <input
              type="range"
              class="w-full"
              v-model.number="examMinScore"
              min="50"
              max="100"
            />
            <div class="flex justify-between text-xs text-[var(--color-text-muted)] mt-1">
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/${temaId}/preguntas`" class="btn btn-secondary btn-block">
            Editar banco de preguntas
          </router-link>
        </div>
      </div>
    </div>
  </div>


  </div>
</template>
