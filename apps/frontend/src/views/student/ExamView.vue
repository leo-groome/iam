<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ExamRunner from '@/components/ui/ExamRunner.vue';
import { findCurso, preguntasMock } from '@/lib/mock';

const route = useRoute();
const router = useRouter();

const id = route.params.id as string;
const temaId = route.params.temaId as string;

const curso = findCurso(id);
if (!curso) {
  router.replace('/catalogo');
}

const tema = computed(() => {
  if (!curso) return null;
  return curso.modulos.flatMap(m => m.temas).find(t => t.id === temaId);
});

if (curso && !tema.value) {
  router.replace(`/curso/${id}`);
}
</script>

<template>
  <div v-if="curso && tema">
    <p class="text-sm text-[var(--color-primary)] font-medium">Cuestionario</p>
    <h1 class="text-2xl sm:text-3xl font-bold tracking-tight mb-6">{{ tema.title }}</h1>

    <ExamRunner :preguntas="preguntasMock" :cursoId="id" :temaId="temaId" :minPercent="70" />

    <div class="h-32"></div>
  </div>
</template>
