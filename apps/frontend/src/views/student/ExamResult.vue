<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const router = useRouter();

const slug = route.params.slug as string;
const topicId = route.params.topicId as string;

const curso = ref(null);
const loading = ref(true);

onMounted(async () => {
  try {
    curso.value = await coursesService.getBySlug(slug);
  } catch (err) {
    console.error(err);
    router.replace('/catalogo');
  } finally {
    loading.value = false;
  }
});

const allTemas = computed(() => {
  if (!curso.value) return [];
  return curso.value.modules.flatMap(m => m.topics);
});
const idx = computed(() => allTemas.value.findIndex(t => t.id === topicId));
const next = computed(() => allTemas.value[idx.value + 1]);
</script>

<template>
  <div v-if="!loading && curso">
    <div class="card p-8 text-center max-w-md mx-auto mt-8">
      <div class="text-6xl mb-3">🎉</div>
      <h1 class="text-3xl font-bold">¡Bien hecho!</h1>
      <p class="text-[var(--color-text-muted)] mt-2">Tema aprobado. Sigues avanzando.</p>
      <router-link :to="next ? `/curso/${slug}/tema/${next.id}` : `/curso/${slug}/certificado`"
         class="btn btn-primary btn-block mt-6">
        {{ next ? 'Continuar al siguiente tema' : 'Ver mi certificado' }}
      </router-link>
      <router-link :to="`/curso/${slug}`" class="btn btn-ghost btn-block mt-2">Volver al curso</router-link>
    </div>
  </div>
</template>
