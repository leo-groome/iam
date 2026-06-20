<script setup lang="ts">
import { useRoute } from 'vue-router';
import { onMounted, ref } from 'vue';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const slug = route.params.slug as string;
const modId = route.params.modId as string;
const topicId = route.params.topicId as string;

const isNew = topicId === 'nuevo';
const curso = ref(null);
const mod = ref(null);
const tema = ref(null);
const loading = ref(false);

onMounted(async () => {
  loading.value = true;
  try {
    curso.value = await coursesService.getBySlug(slug);
    mod.value = curso.value?.modules.find(m => m.id === modId);
    if (!isNew) {
      tema.value = mod.value?.topics.find(t => t.id === topicId);
    }
  } catch (err) {
    console.error('Error loading course:', err);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page-container">


  <router-link :to="`/admin/cursos/${slug}/modulos/${modId}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Módulo</router-link>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Nuevo tema" : `Editar: ${tema?.title}` }}</h1>
    <button class="btn btn-primary">Guardar</button>
  </header>

  <div class="grid lg:grid-cols-3 gap-6">
    <div class="card p-6 lg:col-span-2 space-y-4">
      <div>
        <label class="label">Título</label>
        <input class="input" minlength="3" maxlength="60" :value="tema?.title ?? ''" />
      </div>
      <div>
        <label class="label">Tipo de contenido</label>
        <select class="input">
          <option value="video" :selected="tema?.type === 'video'">Video</option>
          <option value="pdf" :selected="tema?.type === 'pdf'">PDF</option>
          <option value="imagen" :selected="tema?.type === 'imagen'">Imagen / Infografía</option>
          <option value="texto" :selected="tema?.type === 'texto'">Texto enriquecido</option>
        </select>
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
          <input type="checkbox" :checked="tema?.hasExam" />
        </label>
        <router-link v-if="tema?.hasExam" :to="`/admin/cursos/${id}/modulos/${modId}/temas/${temaId}/preguntas`" class="btn btn-secondary btn-block mt-4">
          Editar banco de preguntas
        </router-link>
      </div>
    </div>
  </div>


  </div>
</template>
