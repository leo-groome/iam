<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { findCurso } from '@/lib/mock';

const route = useRoute();
const router = useRouter();

const id = route.params.id as string;
const temaId = route.params.temaId as string;

const curso = findCurso(id);
if (!curso) {
  router.replace('/catalogo');
}

const allTemas = computed(() => {
  if (!curso) return [];
  return curso.modulos.flatMap(m => m.temas);
});
const idx = computed(() => allTemas.value.findIndex(t => t.id === temaId));
const next = computed(() => allTemas.value[idx.value + 1]);
</script>

<template>
  <div v-if="curso">
    <div class="card p-8 text-center max-w-md mx-auto mt-8">
      <div class="text-6xl mb-3">🎉</div>
      <h1 class="text-3xl font-bold">¡Bien hecho!</h1>
      <p class="text-[var(--color-text-muted)] mt-2">Tema aprobado. Sigues avanzando.</p>
      <router-link :to="next ? `/curso/${id}/tema/${next.id}` : `/curso/${id}/certificado`"
         class="btn btn-primary btn-block mt-6">
        {{ next ? 'Continuar al siguiente tema' : 'Ver mi certificado' }}
      </router-link>
      <router-link :to="`/curso/${id}`" class="btn btn-ghost btn-block mt-2">Volver al curso</router-link>
    </div>
  </div>
</template>
