<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProgressBar from '@/components/ui/ProgressBar.vue';
import { findCurso } from '@/lib/mock';

const route = useRoute();
const router = useRouter();
const id = route.params.id as string;

const curso = findCurso(id);
if (!curso) {
  router.replace('/catalogo');
}

const totalTemas = computed(() => {
  if (!curso) return 0;
  return curso.modulos.flatMap(m => m.temas).length;
});

const aprobados = computed(() => {
  if (!curso) return 0;
  return curso.modulos.flatMap(m => m.temas).filter(t => t.status === 'aprobado').length;
});
</script>

<template>
  <div v-if="curso">
    <router-link :to="`/curso/${id}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Volver al curso</router-link>

    <h1 class="text-3xl font-bold mb-2">Mi progreso</h1>
    <p class="text-[var(--color-text-muted)] mb-6">{{ curso.title }}</p>

    <div class="card p-6 mb-6">
      <ProgressBar :value="curso.progress" showPercent label="Progreso total" />
      <p class="text-sm text-[var(--color-text-muted)] mt-4">{{ aprobados }} de {{ totalTemas }} temas completados</p>
    </div>

    <div class="space-y-4">
      <div v-for="(mod, mi) in curso.modulos" :key="mod.id || mi" class="card p-5">
        <div class="flex items-start justify-between gap-3 mb-3">
          <div>
            <p class="text-xs text-[var(--color-text-muted)]">Módulo {{ mi + 1 }}</p>
            <h3 class="font-semibold">{{ mod.title }}</h3>
          </div>
          <span class="chip">{{ Math.round((mod.temas.filter(t => t.status === 'aprobado').length / mod.temas.length) * 100) }}%</span>
        </div>
        <ul class="space-y-1.5">
          <li v-for="(t, ti) in mod.temas" :key="t.id || ti" class="flex items-center gap-2 text-sm">
            <span :class="`w-5 h-5 rounded-full grid place-items-center text-[10px] font-bold ${t.status === 'aprobado' ? 'bg-emerald-100 text-emerald-700' : t.status === 'bloqueado' ? 'bg-[var(--color-app-bg)] text-[var(--color-text-muted)]' : 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]'}`">
              {{ t.status === 'aprobado' ? '✓' : '' }}
            </span>
            <span :class="t.status === 'bloqueado' ? 'text-[var(--color-text-muted)]' : ''">{{ t.title }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
