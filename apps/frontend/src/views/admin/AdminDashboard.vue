<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import StatCard from "@/components/ui/StatCard.vue";
import SkeletonStats from "@/components/ui/SkeletonStats.vue";
import Banner from "@/components/ui/Banner.vue";
import { adminService } from '@/services/admin.service';

const kpis = ref<any>(null);
const loading = ref(true);
const maxWeekly = computed(() => Math.max(1, ...(kpis.value?.enrollments_per_week ?? []).map((w: any) => w.count)));
const maxCompletions = computed(() => Math.max(1, ...(kpis.value?.completions_per_course ?? []).map((c: any) => c.completions)));

onMounted(async () => {
  try {
    kpis.value = await adminService.getDashboardKpis();
  } catch (err) {
    console.error('Error loading dashboard KPIs:', err);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-8 pb-12 animate-fade-in">
    <header class="flex flex-col gap-1">
      <h1 class="text-3xl font-bold text-[var(--color-text)] tracking-tight">Hola de nuevo 👋</h1>
      <p class="text-[var(--color-text-muted)]">Aquí tienes el resumen del rendimiento de tu plataforma académica.</p>
    </header>

    <!-- ALERTS -->
    <transition name="fade" mode="out-in">
      <div v-if="!loading && kpis?.stuck_students > 0" class="flex items-center gap-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200 p-4 rounded-xl shadow-sm">
        <div class="bg-amber-100 dark:bg-amber-800/50 p-2 rounded-full">
          <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
        </div>
        <div>
          <h3 class="font-bold">Atención Requerida: {{ kpis?.stuck_students }} estudiantes atorados</h3>
          <p class="text-sm opacity-90">Tienen 3 o más intentos fallidos consecutivos. Revisa el reporte académico.</p>
        </div>
      </div>
    </transition>

    <!-- MAIN KPIS -->
    <section>
      <h2 class="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)] mb-4">Métricas Globales</h2>
      
      <div v-if="loading" class="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <SkeletonStats v-for="i in 5" :key="i" />
      </div>
      
      <transition name="fade" mode="out-in">
        <div v-if="!loading" class="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard label="Estudiantes Totales" :value="String(kpis?.total_students ?? '-')" :delta="`${kpis?.new_students_last_7d ?? 0} nuevos (7 días)`" trend="up" class="hover:shadow-md transition-shadow" />
          <StatCard label="Cursos Activos" :value="String(kpis?.active_courses ?? '-')" class="hover:shadow-md transition-shadow" />
          <StatCard label="Tasa de Finalización" :value="`${kpis?.completion_rate ?? '-'}%`" class="hover:shadow-md transition-shadow" />
          <StatCard label="Promedio Global" :value="`${kpis?.avg_exam_score ?? '-'}/100`" class="hover:shadow-md transition-shadow" />
          <StatCard label="Certificados Emitidos" :value="String(kpis?.certificates_issued ?? '-')" class="hover:shadow-md transition-shadow" />
        </div>
      </transition>
    </section>

    <!-- DATOS REALES: inscripciones por semana y finalizaciones por curso -->
    <transition name="fade" mode="out-in">
      <div v-if="!loading && kpis" class="grid lg:grid-cols-2 gap-6">
        <div class="card p-6">
          <h2 class="font-bold text-[var(--color-text)] mb-6">Inscripciones por semana</h2>
          <div class="flex items-end gap-1.5 h-40">
            <div v-for="w in kpis.enrollments_per_week" :key="w.week_start" class="flex-1 flex flex-col items-center justify-end gap-1 h-full" :title="`${w.week_start}: ${w.count}`">
              <span class="text-[10px] text-[var(--color-text-muted)]">{{ w.count || '' }}</span>
              <div class="w-full rounded-t bg-[var(--color-primary)]" :style="`height: ${Math.max(2, (w.count / maxWeekly) * 100)}%`"></div>
            </div>
          </div>
          <p class="text-xs text-[var(--color-text-muted)] mt-3">Últimas 12 semanas.</p>
        </div>

        <div class="card p-6">
          <h2 class="font-bold text-[var(--color-text)] mb-6">Finalizaciones por curso</h2>
          <p v-if="!kpis.completions_per_course?.length" class="text-sm text-[var(--color-text-muted)]">Aún nadie ha completado un curso.</p>
          <div v-else class="space-y-5">
            <div v-for="c in kpis.completions_per_course" :key="c.course_id">
              <div class="flex justify-between text-sm mb-2">
                <span class="font-semibold text-[var(--color-text)]">{{ c.title }}</span>
                <span class="text-[var(--color-text-muted)] font-medium">{{ c.completions }}</span>
              </div>
              <div class="h-2.5 bg-[var(--color-bg-hover)] rounded-full overflow-hidden">
                <div class="h-full rounded-full bg-emerald-500" :style="`width: ${(c.completions / maxCompletions) * 100}%`"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
