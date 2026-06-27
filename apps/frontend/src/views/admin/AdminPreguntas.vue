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
</script>

<template>
  <div class="page-container">


  <div class="mb-4 text-sm text-[var(--color-text-muted)] flex items-center gap-2">
    <router-link to="/admin/cursos" class="hover:text-[var(--color-primary)] transition-colors">Cursos</router-link>
    <span>/</span>
    <router-link :to="`/admin/cursos/${courseId}`" class="hover:text-[var(--color-primary)] transition-colors">Curso</router-link>
    <span>/</span>
    <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}`" class="hover:text-[var(--color-primary)] transition-colors">Módulo</router-link>
    <span>/</span>
    <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/${temaId}`" class="hover:text-[var(--color-primary)] transition-colors">{{ tema?.title || 'Tema' }}</router-link>
    <span>/</span>
    <span class="font-medium text-[var(--color-text)]">Preguntas</span>
  </div>
  <header class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold">Banco de preguntas</h1>
      <p class="text-[var(--color-text-muted)]">{{ questions.length }} preguntas activas</p>
    </div>
    <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/${temaId}/preguntas/nueva`" class="btn btn-primary">+ Agregar pregunta</router-link>
  </header>


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
