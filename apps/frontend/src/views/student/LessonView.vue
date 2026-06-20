<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import LearningPlayer from '@/components/ui/LearningPlayer.vue';
import { findCurso } from '@/lib/mock';

const route = useRoute();
const router = useRouter();

const id = route.params.id as string;
const temaId = route.params.temaId as string;
const isRepaso = route.query.repaso === '1';

const curso = findCurso(id);
if (!curso) {
  router.replace('/catalogo');
}

const allTemas = computed(() => {
  if (!curso) return [];
  return curso.modulos.flatMap(m => m.temas.map(t => ({ ...t, moduloTitle: m.title })));
});

const idx = computed(() => allTemas.value.findIndex(t => t.id === temaId));
const tema = computed(() => allTemas.value[idx.value]);

if (curso && !tema.value) {
  router.replace(`/curso/${id}`);
}

const nextTema = computed(() => allTemas.value[idx.value + 1]);
const examUrl = computed(() => `/curso/${id}/tema/${temaId}/examen`);
const nextUrl = computed(() => nextTema.value ? `/curso/${id}/tema/${nextTema.value.id}` : `/curso/${id}/certificado`);
</script>

<template>
  <div v-if="curso && tema">
    <router-link :to="`/curso/${id}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Volver al curso</router-link>

    <div v-if="isRepaso" class="card p-4 mb-4 bg-amber-50 border-amber-200">
      <p class="text-amber-800 text-sm font-medium">📖 Repaso del tema</p>
      <p class="text-amber-700 text-sm mt-1">Vuelve a ver el contenido completo para reintentar el cuestionario.</p>
    </div>

    <p class="text-sm text-[var(--color-primary)] font-medium">{{ tema.moduloTitle }}</p>
    <h1 class="text-2xl sm:text-3xl font-bold tracking-tight mt-1 mb-2">{{ tema.title }}</h1>
    <p class="text-[var(--color-text-muted)] mb-6">{{ tema.duration }} · {{ tema.hasExam ? 'Con examen' : 'Sin examen' }}</p>

    <LearningPlayer
      :type="tema.type"
      :examUrl="examUrl"
      :nextUrl="nextUrl"
      :hasExam="tema.hasExam"
    >
      <h2>Introducción</h2>
      <p>El acompañamiento social es una práctica que requiere atención, escucha activa y respeto absoluto por la dignidad de la persona. En este tema veremos los pilares fundamentales para hacerlo bien.</p>
      <h3>Pilar 1: Atención</h3>
      <p>Estar presente sin distracciones. Mirar a los ojos. Notar el lenguaje corporal.</p>
      <h3>Pilar 2: Escucha</h3>
      <p>Sin interrumpir. Sin juzgar. Validando emociones.</p>
      <h3>Pilar 3: Orientación</h3>
      <p>Solo cuando se solicite. Con información clara y verificada.</p>
    </LearningPlayer>
  </div>
</template>
