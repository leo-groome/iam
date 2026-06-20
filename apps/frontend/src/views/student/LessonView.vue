<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import LearningPlayer from '@/components/ui/LearningPlayer.vue';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const router = useRouter();

const slug = route.params.slug as string;
const topicId = route.params.topicId as string;
const isRepaso = route.query.repaso === '1';

const curso = ref(null);
const allTemas = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    curso.value = await coursesService.getBySlug(slug);
    allTemas.value = curso.value?.modules.flatMap(m => m.topics.map(t => ({ ...t, moduloTitle: m.title }))) || [];
    if (!allTemas.value.find(t => t.id === topicId)) {
      router.replace(`/curso/${slug}`);
    }
  } catch (err) {
    console.error(err);
    router.replace('/catalogo');
  } finally {
    loading.value = false;
  }
});

const idx = computed(() => allTemas.value.findIndex(t => t.id === topicId));
const tema = computed(() => allTemas.value[idx.value]);

const nextTema = computed(() => allTemas.value[idx.value + 1]);
const examUrl = computed(() => `/curso/${slug}/tema/${topicId}/examen`);
const nextUrl = computed(() => nextTema.value ? `/curso/${slug}/tema/${nextTema.value.id}` : `/curso/${slug}/certificado`);
</script>

<template>
  <div v-if="!loading && curso && tema">
    <router-link :to="`/curso/${slug}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Volver al curso</router-link>

    <div v-if="isRepaso" class="card p-4 mb-4 bg-amber-50 border-amber-200">
      <p class="text-amber-800 text-sm font-medium">📖 Repaso del tema</p>
      <p class="text-amber-700 text-sm mt-1">Vuelve a ver el contenido completo para reintentar el cuestionario.</p>
    </div>

    <p class="text-sm text-[var(--color-primary)] font-medium">{{ tema.moduloTitle }}</p>
    <h1 class="text-2xl sm:text-3xl font-bold tracking-tight mt-1 mb-2">{{ tema.title }}</h1>
    <p class="text-[var(--color-text-muted)] mb-6">{{ tema.duration_seconds }}s · {{ tema.has_exam ? 'Con examen' : 'Sin examen' }}</p>

    <LearningPlayer
      :tema="tema"
      :examUrl="examUrl"
      :nextUrl="nextUrl"
      :hasExam="tema.has_exam"
    >
      <div v-html="tema.content_body"></div>
    </LearningPlayer>
  </div>
</template>
