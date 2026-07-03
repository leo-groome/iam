<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ExamRunner from '@/components/ui/ExamRunner.vue';
import SkeletonCard from '@/components/ui/SkeletonCard.vue';
import SkeletonText from '@/components/ui/SkeletonText.vue';
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

const allTemas = computed(() => {
  if (!curso.value) return [];
  return curso.value.modules.flatMap(m => m.topics);
});
const idx = computed(() => allTemas.value.findIndex(t => t.id === topicId));
const nextTema = computed(() => allTemas.value[idx.value + 1]);
const nextUrl = computed(() => {
  return nextTema.value ? `/curso/${slug}/tema/${nextTema.value.id}` : `/curso/${slug}/certificado`;
});
</script>

<template>
  <div class="animate-fade-in">
    <transition name="fade" mode="out-in">
      <div v-if="loading" class="space-y-4">
        <SkeletonText :lines="1" titleWidth="100px" class="mb-4" />
        <SkeletonText :lines="1" titleWidth="250px" class="mb-6 h-8" />
        <SkeletonCard :hasImage="false" :hasIcon="false" :hasSubtitle="true" :hasFooter="true" class="h-64" />
      </div>
      <div v-else-if="curso && tema">
        <p class="text-sm text-[var(--color-primary)] font-medium">Cuestionario</p>
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight mb-6">{{ tema.title }}</h1>

        <ExamRunner :topicId="topicId" :cursoSlug="slug" :nextUrl="nextUrl" />

        <div class="h-32"></div>
      </div>
    </transition>
  </div>
</template>
