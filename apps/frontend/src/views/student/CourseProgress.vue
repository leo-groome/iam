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

const totalTemas = computed(() => {
  if (!curso.value) return 0;
  return curso.value.modules.flatMap(m => m.topics).length;
});

const aprobados = computed(() => {
  if (!curso.value) return 0;
  return curso.value.modules.flatMap(m => m.topics).filter(t => t.state === 'aprobado').length;
});
</script>

<template>
  <div v-if="!loading && curso">
    <router-link :to="`/curso/${slug}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Volver al curso</router-link>

    <h1 class="text-3xl font-bold mb-2">Mi progreso</h1>
    <p class="text-[var(--color-text-muted)] mb-6">{{ curso.title }}</p>

    <div class="card p-6 mb-6">
      <ProgressBar :value="curso.progress_pct" showPercent label="Progreso total" />
      <p class="text-sm text-[var(--color-text-muted)] mt-4">{{ aprobados }} de {{ totalTemas }} temas completados</p>
    </div>

    <div class="space-y-4">
      <div v-for="(mod, mi) in curso.modules" :key="mod.id || mi" class="card p-5">
        <div class="flex items-start justify-between gap-3 mb-3">
          <div>
            <p class="text-xs text-[var(--color-text-muted)]">Módulo {{ mi + 1 }}</p>
            <h3 class="font-semibold">{{ mod.title }}</h3>
          </div>
          <span class="chip">{{ Math.round((mod.topics.filter(t => t.state === 'aprobado').length / mod.topics.length) * 100) }}%</span>
        </div>
        <ul class="space-y-1.5">
          <li v-for="(t, ti) in mod.topics" :key="t.id || ti" class="flex items-center gap-2 text-sm">
            <span :class="`w-5 h-5 rounded-full grid place-items-center text-[10px] font-bold ${t.state === 'aprobado' ? 'bg-emerald-100 text-emerald-700' : t.state === 'bloqueado' ? 'bg-[var(--color-app-bg)] text-[var(--color-text-muted)]' : 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]'}`">
              {{ t.state === 'aprobado' ? '✓' : '' }}
            </span>
            <span :class="t.state === 'bloqueado' ? 'text-[var(--color-text-muted)]' : ''">{{ t.title }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
