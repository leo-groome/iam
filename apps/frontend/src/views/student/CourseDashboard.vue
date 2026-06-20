<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProgressBar from '@/components/ui/ProgressBar.vue';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const router = useRouter();
const slug = route.params.slug as string;

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

const primerTemaPendiente = computed(() => {
  if (!curso.value) return null;
  const all = curso.value.modules.flatMap(m => m.topics);
  return all.find(t => t.state !== 'aprobado') ?? (curso.value.modules[0]?.topics[0] ?? null);
});

const ctaHref = computed(() => {
  if (!curso.value || !primerTemaPendiente.value) return '';
  return `/curso/${curso.value.slug}/tema/${primerTemaPendiente.value.id}`;
});

const ctaLabel = computed(() => {
  if (!curso.value) return '';
  return curso.value.progress_pct > 0 ? 'Continuar' : 'Empezar curso';
});
</script>

<template>
  <div v-if="!loading && curso">
    <router-link to="/catalogo" class="text-sm text-[var(--color-text-muted)] mb-4 inline-block">← Catálogo</router-link>

    <div class="card overflow-hidden mb-6">
      <div class="aspect-[21/9] bg-[var(--color-primary-soft)] overflow-hidden">
        <img :src="curso.cover_key || '/placeholder.jpg'" :alt="curso.title" class="w-full h-full object-cover" />
      </div>
      <div class="p-6 sm:p-8">
        <p class="text-sm text-[var(--color-primary)] font-medium mb-1">{{ curso.short_desc }}</p>
        <h1 class="text-3xl font-bold tracking-tight">{{ curso.title }}</h1>
        <p class="text-[var(--color-text-muted)] mt-3 leading-relaxed">{{ curso.long_desc }}</p>

        <div class="flex flex-wrap gap-2 mt-5">
          <span class="chip">{{ curso.modules.length }} módulos</span>
          <span class="chip">Certificado al terminar</span>
        </div>

        <div class="mt-6">
          <ProgressBar :value="curso.progress_pct" label="Tu progreso" showPercent />
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
            <span :class="`w-7 h-7 rounded-full grid place-items-center text-xs font-semibold ${tema.state === 'aprobado' ? 'bg-emerald-100 text-emerald-700' : tema.state === 'bloqueado' ? 'bg-[var(--color-app-bg)] text-[var(--color-text-muted)]' : 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]'}`">
              {{ tema.state === 'aprobado' ? '✓' : ti + 1 }}
            </span>
            <span :class="tema.state === 'bloqueado' ? 'text-[var(--color-text-muted)]' : ''">{{ tema.title }}</span>
            <span class="ml-auto text-xs text-[var(--color-text-muted)]">{{ tema.duration_seconds }}s</span>
          </li>
        </ul>
      </details>
    </div>

    <div class="fixed bottom-0 left-0 right-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-4 sm:static sm:bg-transparent sm:border-0 sm:p-0">
      <div class="max-w-3xl mx-auto">
        <router-link :to="ctaHref" class="btn btn-primary btn-block">{{ ctaLabel }}</router-link>
      </div>
    </div>
  </div>
</template>
