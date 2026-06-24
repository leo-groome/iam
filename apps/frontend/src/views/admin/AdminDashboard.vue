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
  <div class="page-container">

    <header class="mb-6">
      <h1 class="text-3xl font-bold">Dashboard</h1>
      <p class="text-[var(--color-text-muted)]">Vista general de la plataforma y actividad reciente.</p>
    </header>

    <Banner v-if="kpis?.stuck_students > 0" kind="warning" :title="`${kpis?.stuck_students} estudiantes atorados`">
      Tienen 3+ intentos fallidos en el mismo tema. Revisa quiénes necesitan apoyo.
    </Banner>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
      <StatCard label="Estudiantes Totales" :value="String(kpis?.total_students ?? '-')" delta="+12 este mes" trend="up" />
      <StatCard label="Cursos activos" :value="String(kpis?.active_courses ?? '-')" delta="+5 vs ayer" trend="up" />
      <StatCard label="Tasa de finalización" :value="`${kpis?.completion_rate ?? '-'}%`" delta="+3 esta semana" trend="up" />
      <StatCard label="Promedio Exámenes" :value="`${kpis?.avg_exam_score ?? '-'}/100`" delta="Estable" trend="up" />
    </div>

    <div class="grid lg:grid-cols-2 gap-6 mt-6">
      <!-- Actividad Reciente -->
      <div class="card p-6">
        <h2 class="font-semibold mb-4 text-lg border-b border-[var(--color-border)] pb-2">Actividad Reciente</h2>
        <div class="space-y-4 mt-4">
          <div v-for="(act, index) in [
            { user: 'María González', action: 'obtuvo su certificado en', target: 'Módulo: Educar', time: 'hace 2 horas', icon: '🏆' },
            { user: 'Juan Pérez', action: 'se registró en la plataforma', target: '', time: 'hace 5 horas', icon: '👤' },
            { user: 'Ana López', action: 'completó su examen con', target: '95/100', time: 'ayer', icon: '📝' },
            { user: 'Carlos M.', action: 'comenzó el curso', target: 'Acompañamiento Social', time: 'ayer', icon: '▶️' },
          ]" :key="index" class="flex gap-3 text-sm items-start">
            <div class="text-xl bg-[var(--color-app-bg)] w-8 h-8 rounded-full flex items-center justify-center shrink-0 border border-[var(--color-border)]">{{ act.icon }}</div>
            <div>
              <p><span class="font-semibold text-[var(--color-text)]">{{ act.user }}</span> <span class="text-[var(--color-text-muted)]">{{ act.action }}</span> <span class="font-medium text-[var(--color-primary)]">{{ act.target }}</span></p>
              <p class="text-xs text-[var(--color-text-muted)] mt-0.5">{{ act.time }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Cursos más populares -->
      <div class="card p-6">
        <h2 class="font-semibold mb-4 text-lg border-b border-[var(--color-border)] pb-2">Módulos más activos</h2>
        <div class="space-y-5 mt-4">
          <div v-for="c in [
            { name: '1. Educar en la fe', active: 120, pct: 85 },
            { name: '2. Acompañamiento social', active: 85, pct: 60 },
            { name: '3. Proteger la vida', active: 43, pct: 30 },
          ]" :key="c.name">
            <div class="flex justify-between text-sm mb-1">
              <span class="font-medium">{{ c.name }}</span>
              <span class="text-[var(--color-text-muted)]">{{ c.active }} activos</span>
            </div>
            <div class="h-2 bg-[var(--color-primary-soft)] rounded-full overflow-hidden">
              <div class="h-full bg-[var(--color-primary)]" :style="`width: ${c.pct}%`"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
