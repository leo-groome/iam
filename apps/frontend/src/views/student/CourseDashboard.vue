<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProgressBar from '@/components/ui/ProgressBar.vue';
import SkeletonCard from '@/components/ui/SkeletonCard.vue';
import SkeletonText from '@/components/ui/SkeletonText.vue';
import { coursesService } from '@/services/courses.service';
import { sanitizeHtml } from '@/lib/sanitize';
import { useProgressStore } from '@/stores/progress';

const route = useRoute();
const router = useRouter();
const slug = route.params.slug as string;
const progressStore = useProgressStore();

const curso = ref(null);
const loading = ref(true);

onMounted(async () => {
  try {
    curso.value = await coursesService.getBySlug(slug);
    
    // Dynamically calculate accurate progress in case backend is stale
    const allTemas = curso.value.modules.flatMap((m: any) => m.topics);
    const isDone = (t: any) => t.has_exam ? t.state === 'aprobado' : ['contenido_visto', 'aprobado', 'en_repaso'].includes(t.state);
    const alreadyDone = allTemas.filter(isDone).length;
    const computedPct = allTemas.length > 0 ? Math.round((alreadyDone / allTemas.length) * 100) : 0;
    
    progressStore.hydrate(slug, { course_pct: Math.max(curso.value.progress_pct, computedPct), modules: [] });
    
    if (route.query.auto_resume === '1' && progressStore.coursePercentage(slug) > 0 && progressStore.coursePercentage(slug) < 100) {
      if (primerTemaPendiente.value) {
        router.replace(`/curso/${slug}/tema/${primerTemaPendiente.value.id}`);
        return;
      }
    }
  } catch (err) {
    console.error(err);
    router.replace('/catalogo');
  } finally {
    loading.value = false;
  }
});

const joining = ref(false);
const coverLoaded = ref(false);

const isCompleted = computed(() => {
  if (!curso.value) return false;
  return curso.value.enrollment_status === 'completado' || progressStore.coursePercentage(slug) === 100;
});

const primerTemaPendiente = computed(() => {
  if (!curso.value) return null;
  const all = curso.value.modules.flatMap((m: any) => m.topics);
  const isDone = (t: any) => t.has_exam ? t.state === 'aprobado' : ['contenido_visto', 'aprobado', 'en_repaso'].includes(t.state);
  return all.find(t => !isDone(t)) ?? (curso.value.modules[0]?.topics[0] ?? null);
});

const ctaHref = computed(() => {
  if (!curso.value) return '';
  if (isCompleted.value) return `/curso/${curso.value.slug}/certificado`;
  if (!primerTemaPendiente.value) return `/curso/${curso.value.slug}/certificado`;
  return `/curso/${curso.value.slug}/tema/${primerTemaPendiente.value.id}`;
});

const ctaLabel = computed(() => {
  if (!curso.value) return '';
  if (curso.value.enrollment_status === 'no_iniciado') {
    return 'Inscribirse al curso';
  }
  if (isCompleted.value) return 'Ver Certificado';
  return progressStore.coursePercentage(slug) > 0 ? 'Continuar' : 'Empezar curso';
});

async function handleCtaClick() {
  if (!curso.value || !primerTemaPendiente.value || joining.value) return;
  joining.value = true;

  if (curso.value.enrollment_status === 'no_iniciado') {
    // Optimistic: update local state + navigate immediately.
    // Enrollment fires in background — LessonView retries on mount if this fails.
    curso.value.enrollment_status = 'en_progreso';
    coursesService.enroll(slug).catch(err => console.error('Background enrollment failed:', err));
  }

  router.push(ctaHref.value);
}
</script>

<template>
  <div class="animate-fade-in">
    <transition name="fade" mode="out-in">
      <div v-if="loading" class="space-y-6">
        <SkeletonText :lines="1" titleWidth="100px" class="mb-4" />
        <SkeletonCard :hasImage="true" :hasIcon="false" :hasSubtitle="true" :hasFooter="true" class="mb-6 h-[400px]" />
        <SkeletonText :lines="1" titleWidth="150px" class="mb-3" />
        <div class="space-y-3 mb-8">
          <SkeletonCard v-for="i in 3" :key="i" :hasImage="false" :hasIcon="true" :hasSubtitle="false" :hasFooter="false" />
        </div>
      </div>
      <div v-else-if="curso">
        <router-link to="/catalogo" class="text-sm text-[var(--color-text-muted)] mb-4 inline-block">← Catálogo</router-link>

        <div class="card overflow-hidden mb-6">
          <div class="aspect-[21/9] bg-[var(--color-primary-soft)] overflow-hidden relative">
            <div
              v-if="!coverLoaded"
              class="absolute inset-0 bg-[var(--color-border)] animate-pulse"
            ></div>
            <img
              :src="curso.cover_key || '/placeholder.jpg'"
              :alt="curso.title"
              class="w-full h-full object-cover transition-opacity duration-500"
              :class="coverLoaded ? 'opacity-100' : 'opacity-0'"
              loading="lazy"
              @load="coverLoaded = true"
            />
          </div>
          <div class="p-6 sm:p-8">
            <p class="text-sm text-[var(--color-primary)] font-medium mb-1 rich-text" v-html="sanitizeHtml(curso.short_desc)"></p>
            <h1 class="text-3xl font-bold tracking-tight">{{ curso.title }}</h1>
            <div class="text-[var(--color-text-muted)] mt-3 leading-relaxed rich-text" v-html="sanitizeHtml(curso.long_desc)"></div>

            <div class="flex flex-wrap gap-2 mt-5">
              <span class="chip">{{ curso.modules.length }} módulos</span>
              <span class="chip">Certificado al terminar</span>
            </div>

            <div class="mt-6">
              <ProgressBar :value="progressStore.coursePercentage(slug)" label="Tu progreso" showPercent />
            </div>
          </div>
        </div>

        <h2 class="text-lg font-semibold mb-3">Contenido del curso</h2>
        <div class="space-y-3 mb-8">
          <details v-for="(mod, idx) in curso.modules" :key="mod.id || idx" class="card p-5" :open="idx === 0">
            <summary class="flex items-start justify-between gap-3 cursor-pointer list-none">
              <div class="flex-1 min-w-0">
                <p class="text-xs text-[var(--color-text-muted)] mb-1">Módulo {{ idx + 1 }}</p>
                <h3 class="font-semibold">{{ mod.title }}</h3>
              </div>
            </summary>
            <ul class="mt-4 space-y-2 border-t border-[var(--color-border)] pt-4">
              <li v-for="(tema, ti) in mod.topics" :key="tema.id || ti" class="flex items-center gap-3 text-sm">
                <span :class="`w-7 h-7 rounded-full grid place-items-center text-xs font-semibold ${(tema.has_exam ? tema.state === 'aprobado' : ['contenido_visto', 'aprobado', 'en_repaso'].includes(tema.state)) ? 'bg-emerald-100 text-emerald-700' : tema.state === 'bloqueado' ? 'bg-[var(--color-app-bg)] text-[var(--color-text-muted)]' : 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]'}`">
                  {{ (tema.has_exam ? tema.state === 'aprobado' : ['contenido_visto', 'aprobado', 'en_repaso'].includes(tema.state)) ? '✓' : ti + 1 }}
                </span>
                <span :class="tema.state === 'bloqueado' ? 'text-[var(--color-text-muted)]' : ''">{{ tema.title }}</span>
                <span class="ml-auto text-xs text-[var(--color-text-muted)]">{{ tema.duration_seconds }}s</span>
              </li>
            </ul>
          </details>
        </div>

        <div class="fixed bottom-0 left-0 right-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-4 sm:static sm:bg-transparent sm:border-0 sm:p-0">
          <div class="max-w-3xl mx-auto">
            <button @click="handleCtaClick" :disabled="joining" class="btn btn-primary btn-block">
              {{ ctaLabel }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
