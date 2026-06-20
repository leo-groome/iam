<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ExamRunner from '@/components/ui/ExamRunner.vue';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const router = useRouter();

const slug = route.params.slug as string;
const topicId = route.params.topicId as string;

const curso = ref(null);
const tema = ref(null);
const loading = ref(true);

onMounted(async () => {
  try {
    curso.value = await coursesService.getBySlug(slug);
    tema.value = curso.value?.modules.flatMap(m => m.topics).find(t => t.id === topicId);
    if (!tema.value) {
      router.replace(`/curso/${slug}`);
    }
  } catch (err) {
    console.error(err);
    router.replace('/catalogo');
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div v-if="!loading && curso && tema">
    <p class="text-sm text-[var(--color-primary)] font-medium">Cuestionario</p>
    <h1 class="text-2xl sm:text-3xl font-bold tracking-tight mb-6">{{ tema.title }}</h1>

    <ExamRunner :topicId="topicId" :cursoSlug="slug" />

    <div class="h-32"></div>
  </div>
</template>
