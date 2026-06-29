<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import LearningPlayer from '@/components/ui/LearningPlayer.vue';
import SkeletonCard from '@/components/ui/SkeletonCard.vue';
import SkeletonText from '@/components/ui/SkeletonText.vue';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const router = useRouter();

const slug = route.params.slug as string;
const topicId = computed(() => route.params.topicId as string);
const isRepaso = route.query.repaso === '1';

const curso = ref(null);
const allTemas = ref([]);
const loading = ref(true);
const temaCargado = ref(null);
const loadingTema = ref(false);

async function fetchTemaDetalle(id: string) {
  temaCargado.value = null; // Reset to avoid showing stale media
  loadingTema.value = true;
  try {
    temaCargado.value = await coursesService.getTopic(id);
  } catch (err) {
    console.error('Error al obtener detalles del tema:', err);
  } finally {
    loadingTema.value = false;
  }
}

onMounted(async () => {
  try {
    curso.value = await coursesService.getBySlug(slug);

    if (curso.value?.enrollment_status === 'no_iniciado') {
      await coursesService.enroll(slug);
      curso.value.enrollment_status = 'en_progreso';
    }

    allTemas.value = curso.value?.modules.flatMap(m => m.topics.map(t => ({ ...t, moduloTitle: m.title }))) || [];
    if (!allTemas.value.find(t => t.id === topicId.value)) {
      router.replace(`/curso/${slug}`);
      return;
    }

    await fetchTemaDetalle(topicId.value);
  } catch (err) {
    console.error(err);
    router.replace('/catalogo');
  } finally {
    loading.value = false;
  }
});

watch(topicId, async (newId) => {
  if (newId && !loading.value) {
    await fetchTemaDetalle(newId);
  }
});

const idx = computed(() => allTemas.value.findIndex(t => t.id === topicId.value));
const tema = computed(() => {
  const rawTopic = allTemas.value[idx.value];
  if (!rawTopic) return null;
  return {
    ...rawTopic,
    ...temaCargado.value
  };
});

const nextTema = computed(() => allTemas.value[idx.value + 1]);
const examUrl = computed(() => `/curso/${slug}/tema/${topicId.value}/examen`);
const nextUrl = computed(() => nextTema.value ? `/curso/${slug}/tema/${nextTema.value.id}` : `/curso/${slug}/certificado`);
</script>

<template>
  <div class="animate-fade-in">
    <transition name="fade" mode="out-in">
      <div v-if="loading" class="space-y-4">
        <SkeletonText :lines="1" titleWidth="100px" class="mb-4" />
        <SkeletonText :lines="1" titleWidth="150px" />
        <SkeletonText :lines="1" titleWidth="250px" class="mb-6 h-8" />
        <SkeletonCard :hasImage="true" :hasIcon="false" :hasSubtitle="false" :hasFooter="true" class="h-[500px]" />
      </div>

      <div v-else-if="curso && tema">
        <router-link :to="`/curso/${slug}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Volver al curso</router-link>

        <div v-if="isRepaso" class="card p-4 mb-4 bg-amber-50 border-amber-200">
          <p class="text-amber-800 text-sm font-medium">📖 Repaso del tema</p>
          <p class="text-amber-700 text-sm mt-1">Vuelve a ver el contenido completo para reintentar el cuestionario.</p>
        </div>

        <p class="text-sm text-[var(--color-primary)] font-medium">{{ tema.moduloTitle }}</p>
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight mt-1 mb-2">{{ tema.title }}</h1>
        <p class="text-[var(--color-text-muted)] mb-6">{{ tema.duration_seconds }}s · {{ tema.has_exam ? 'Con examen' : 'Sin examen' }}</p>

        <transition name="fade" mode="out-in">
          <div v-if="loadingTema" class="card h-[500px] flex items-center justify-center">
             <div class="animate-pulse w-full h-full bg-[var(--color-border)] opacity-30 rounded-2xl"></div>
          </div>
          <LearningPlayer
            v-else
            :tema="tema"
            :examUrl="examUrl"
            :nextUrl="nextUrl"
            :hasExam="tema.has_exam"
          >
            <div v-html="tema.content_body"></div>
          </LearningPlayer>
        </transition>
      </div>
    </transition>
  </div>
</template>
