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
        <div class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-6 text-center hover:bg-[var(--color-app-bg)] transition-colors relative cursor-pointer group">
          <input type="file" accept="video/mp4, video/webm, application/pdf" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
          <div class="space-y-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="text-sm text-[var(--color-text-muted)]">Arrastra o haz clic para subir</p>
            <p class="text-xs text-[var(--color-text-muted)]">Video (mp4/webm, máx 500 MB) o PDF (máx 50 MB).</p>
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
