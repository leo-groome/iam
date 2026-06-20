<script setup lang="ts">
import StatCard from "@/components/ui/StatCard.vue";
import Banner from "@/components/ui/Banner.vue";
</script>

<template>
  <div class="page-container">


  <header class="mb-6">
    <h1 class="text-3xl font-bold">Dashboard</h1>
    <p class="text-[var(--color-text-muted)]">Vista general de la plataforma.</p>
  </header>

  <Banner kind="warning" title="3 estudiantes atorados">
    Tienen 3+ intentos fallidos en el mismo tema. Revisa quiénes necesitan apoyo.
  </Banner>

  <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
    <StatCard label="Estudiantes" value="248" delta="+12 esta semana" trend="up" />
    <StatCard label="Cursos activos" value="3" />
    <StatCard label="Tasa de finalización" value="62%" delta="+4 pts" trend="up" />
    <StatCard label="Promedio" value="84/100" delta="−2 pts" trend="down" />
  </div>

  <div class="grid lg:grid-cols-2 gap-6 mt-6">
    <div class="card p-6">
      <h2 class="font-semibold mb-4">Inscripciones por semana</h2>
      <div class="h-40 flex items-end gap-2">
        <div v-for="(h, index) in [40, 65, 50, 75, 90, 70, 85]" :key="index" class="flex-1 bg-[var(--color-primary)] rounded-t" :style="`height: ${h}%`"></div>
      </div>
      <div class="flex justify-between text-xs text-[var(--color-text-muted)] mt-2">
        <span>L</span><span>M</span><span>M</span><span>J</span><span>V</span><span>S</span><span>D</span>
      </div>
    </div>
    <div class="card p-6">
      <h2 class="font-semibold mb-4">Finalizaciones por curso</h2>
      <div class="space-y-3">
        <div v-for="c in [
          { name: 'Acompañamiento social', pct: 78 },
          { name: 'Primeros auxilios emocionales', pct: 45 },
          { name: 'Comunicación empática', pct: 92 },
        ]" :key="c.name">
          <div class="flex justify-between text-sm mb-1">
            <span>{{ c.name }}</span>
            <span class="font-semibold">{{ c.pct }}%</span>
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
