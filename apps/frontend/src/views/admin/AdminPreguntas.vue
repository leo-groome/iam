<script setup lang="ts">
import { useRoute } from 'vue-router';
import { onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';
import { apiGet } from '@/lib/api';

const route = useRoute();
const courseId = route.params.id as string;
const modId = route.params.modId as string;
const temaId = route.params.temaId as string;

const tema = ref(null);
const questions = ref([]);
const loading = ref(false);
const minScore = ref(70);

onMounted(async () => {
  loading.value = true;
  try {
    const res = await (apiGet as any)('/api/v1/admin/topics/' + temaId);
    tema.value = res;
    questions.value = res.questions ?? [];
    minScore.value = res.exam_min_score ?? 70;
  } catch (err) {
    console.error('Error loading topic:', err);
  } finally {
    loading.value = false;
  }
});

const handleDeleteQuestion = async (qId: string) => {
  try {
    await adminService.archiveQuestion(qId);
    questions.value = questions.value.filter(q => q.id !== qId);
  } catch (err) {
    console.error('Error deleting question:', err);
  }
};

const handleSaveMinScore = async () => {
  try {
    await adminService.updateTopic(temaId, { exam_min_score: minScore.value });
  } catch (err) {
    console.error('Error saving min score:', err);
  }
};
</script>

<template>
  <div class="page-container">


  <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/${temaId}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Tema</router-link>
  <header class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold">Banco de preguntas</h1>
      <p class="text-[var(--color-text-muted)]">{{ questions.length }} preguntas activas</p>
    </div>
    <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/${temaId}/preguntas/nueva`" class="btn btn-primary">+ Agregar pregunta</router-link>
  </header>

  <div class="card p-6 mb-6">
    <label class="label">% mínimo para aprobar</label>
    <div class="flex items-center gap-3">
      <input type="number" class="input max-w-32" min="50" max="100" v-model.number="minScore" @blur="handleSaveMinScore" />
      <p class="text-sm text-[var(--color-text-muted)]">Mínimo 50, máximo 100. Default 70.</p>
    </div>
  </div>

  <div class="space-y-3">
    <div v-for="(p, i) in questions" :key="p.id" class="card p-5">
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <p class="text-xs text-[var(--color-text-muted)] mb-1">Pregunta {{ i + 1 }}</p>
          <p class="font-semibold">{{ p.enunciado }}</p>
          <ul class="mt-3 space-y-1 text-sm">
            <li v-for="(opt, oi) in p.options" :key="opt.id" :class="['flex items-center gap-2', opt.is_correct ? 'text-emerald-700 font-medium' : 'text-[var(--color-text-muted)]']">
              <span>{{ opt.is_correct ? '✓' : '○' }}</span>
              <span>{{ opt.texto }}</span>
            </li>
          </ul>
        </div>
        <div class="flex gap-2">
          <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/${temaId}/preguntas/${p.id}`" class="btn btn-secondary">Editar</router-link>
          <button @click="handleDeleteQuestion(p.id)" class="btn btn-secondary text-[var(--color-error)]">Eliminar</button>
        </div>
      </div>
    </div>
  </div>


  </div>
</template>
