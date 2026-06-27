<script setup lang="ts">
import { ref, onMounted } from 'vue';
import StatCard from "@/components/ui/StatCard.vue";
import Banner from "@/components/ui/Banner.vue";
import { adminService } from '@/services/admin.service';

const kpis = ref<any>(null);
const loading = ref(true);

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
    <div v-if="kpis?.stuck_students > 0" class="flex items-center gap-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200 p-4 rounded-xl shadow-sm">
      <div class="bg-amber-100 dark:bg-amber-800/50 p-2 rounded-full">
        <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
      </div>
      <div>
        <h3 class="font-bold">Atención Requerida: {{ kpis?.stuck_students }} estudiantes atorados</h3>
        <p class="text-sm opacity-90">Tienen 3 o más intentos fallidos consecutivos. Revisa el reporte académico.</p>
      </div>
    </div>

    <!-- MAIN KPIS -->
    <section>
      <h2 class="text-sm font-bold uppercase tracking-wider text-[var(--color-text-muted)] mb-4">Métricas Globales</h2>
      <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Estudiantes Totales" :value="String(kpis?.total_students ?? '-')" delta="+12 este mes" trend="up" class="hover:shadow-md transition-shadow" />
        <StatCard label="Cursos Activos" :value="String(kpis?.active_courses ?? '-')" delta="+5 vs ayer" trend="up" class="hover:shadow-md transition-shadow" />
        <StatCard label="Tasa de Finalización" :value="`${kpis?.completion_rate ?? '-'}%`" delta="+3% esta semana" trend="up" class="hover:shadow-md transition-shadow" />
        <StatCard label="Promedio Global" :value="`${kpis?.avg_exam_score ?? '-'}/100`" delta="Estable" trend="up" class="hover:shadow-md transition-shadow" />
        <StatCard label="Certificados Emitidos" value="142" delta="+28 este mes" trend="up" class="hover:shadow-md transition-shadow" />
      </div>
    </section>

    <div class="grid lg:grid-cols-3 gap-6">
      <!-- ACTIVIDAD RECIENTE (Takes 1 column) -->
      <div class="card flex flex-col hover:shadow-md transition-shadow">
        <div class="p-6 border-b border-[var(--color-border)] flex items-center justify-between">
          <h2 class="font-bold text-[var(--color-text)]">Actividad Reciente</h2>
          <button class="text-xs font-medium text-[var(--color-primary)] hover:underline">Ver todo</button>
        </div>
        <div class="p-6 space-y-6 flex-1 overflow-y-auto max-h-[400px] scrollbar-thin">
          <div v-for="(act, index) in [
            { user: 'María González', action: 'obtuvo su certificado en', target: 'Módulo: Educar', time: 'hace 2 horas', icon: '🏆', color: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
            { user: 'Juan Pérez', action: 'se registró en la plataforma', target: '', time: 'hace 5 horas', icon: '👤', color: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' },
            { user: 'Ana López', action: 'completó su examen con', target: '95/100', time: 'ayer', icon: '📝', color: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
            { user: 'Carlos M.', action: 'comenzó el curso', target: 'Acompañamiento Social', time: 'ayer', icon: '▶️', color: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' },
          ]" :key="index" class="flex gap-4 items-start">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center shrink-0 text-lg shadow-sm', act.color]">
              {{ act.icon }}
            </div>
            <div class="pt-0.5">
              <p class="text-sm leading-snug">
                <span class="font-bold text-[var(--color-text)]">{{ act.user }}</span> 
                <span class="text-[var(--color-text-muted)]"> {{ act.action }} </span> 
                <span class="font-semibold text-[var(--color-primary)]">{{ act.target }}</span>
              </p>
              <p class="text-xs text-[var(--color-text-muted)] mt-1 font-medium uppercase tracking-wide">{{ act.time }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- INSIGHTS (Takes 2 columns) -->
      <div class="lg:col-span-2 space-y-6 flex flex-col">
        <!-- MODULOS ACTIVOS -->
        <div class="card p-6 flex-1 hover:shadow-md transition-shadow">
          <h2 class="font-bold text-[var(--color-text)] mb-6">Rendimiento de Módulos</h2>
          <div class="space-y-6">
            <div v-for="c in [
              { name: '1. Educar en la fe', active: 120, pct: 85, color: 'bg-indigo-500' },
              { name: '2. Acompañamiento social', active: 85, pct: 60, color: 'bg-emerald-500' },
              { name: '3. Proteger la vida', active: 43, pct: 30, color: 'bg-rose-500' },
            ]" :key="c.name" class="group">
              <div class="flex justify-between text-sm mb-2">
                <span class="font-semibold text-[var(--color-text)]">{{ c.name }}</span>
                <span class="text-[var(--color-text-muted)] font-medium">{{ c.active }} activos</span>
              </div>
              <div class="h-2.5 bg-[var(--color-bg-hover)] rounded-full overflow-hidden shadow-inner">
                <div class="h-full rounded-full transition-all duration-500 ease-out group-hover:brightness-110" :class="c.color" :style="`width: ${c.pct}%`"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- ALERTAS CUELLOS DE BOTELLA -->
        <div class="card p-6 hover:shadow-md transition-shadow">
          <div class="flex items-center gap-2 mb-6">
            <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            <h2 class="font-bold text-[var(--color-text)]">Cuellos de Botella Académicos</h2>
          </div>
          <div class="grid md:grid-cols-3 gap-4">
            <div v-for="b in [
              { name: 'Examen Final - Módulo 2', metric: '65% reprueban (1er intento)', severity: 'high', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', class: 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-900/50', iconColor: 'text-red-600 dark:text-red-400', metricColor: 'text-red-700 dark:text-red-300' },
              { name: 'Lectura: Documentos del concilio', metric: '40% de abandono aquí', severity: 'medium', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', class: 'bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-900/50', iconColor: 'text-amber-600 dark:text-amber-400', metricColor: 'text-amber-700 dark:text-amber-300' },
              { name: 'Quiz: Introducción', metric: '25% reprueban (1er intento)', severity: 'low', icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', class: 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-900/50', iconColor: 'text-blue-600 dark:text-blue-400', metricColor: 'text-blue-700 dark:text-blue-300' },
            ]" :key="b.name" :class="['p-4 rounded-xl border flex flex-col justify-between gap-3 transition-colors', b.class]">
              <div class="flex items-start justify-between">
                <svg class="w-6 h-6" :class="b.iconColor" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="b.icon"></path></svg>
              </div>
              <div>
                <h3 class="font-bold text-sm mb-1 leading-tight text-[var(--color-text)]">{{ b.name }}</h3>
                <p class="text-xs font-bold" :class="b.metricColor">{{ b.metric }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
