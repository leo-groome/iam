<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ExamRunner from '@/components/ui/ExamRunner.vue';
import SkeletonCard from '@/components/ui/SkeletonCard.vue';
import SkeletonText from '@/components/ui/SkeletonText.vue';
import { coursesService } from '@/services/courses.service';
import type { CourseDetail } from '@/lib/api';

const route = useRoute();
const router = useRouter();

const slug = route.params.slug as string;
const topicId = route.params.topicId as string | undefined;
const moduleId = route.params.moduleId as string | undefined;

const curso = ref<CourseDetail | null>(null);
const tema = ref<any>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    curso.value = await coursesService.getBySlug(slug);
    tema.value = moduleId
      ? curso.value?.modules.find((m: any) => m.id === moduleId)
      : curso.value?.modules.flatMap((m: any) => m.topics).find((t: any) => t.id === topicId);
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
  if (moduleId) return `/curso/${slug}`;
  const module = curso.value?.modules.find((m: any) => m.topics.some((t: any) => t.id === topicId));
  if (module?.has_exam && !module.exam_passed && module.topics.at(-1)?.id === topicId) return `/curso/${slug}/modulo/${module.id}/examen`;
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

        <ExamRunner :topicId="topicId"
          :moduleId="moduleId" :cursoSlug="slug" :nextUrl="nextUrl" />

        <div class="h-32"></div>
      </div>
    </transition>
  </div>
</template>
