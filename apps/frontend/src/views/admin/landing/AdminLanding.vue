<template>
  <div class="page-container">
    <header class="flex flex-col gap-4 mb-6 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="text-3xl font-bold">Pagina web</h1>
        <p class="text-[var(--color-text-muted)]">Administra el contenido visible de la landing publica.</p>
      </div>
      <a href="/" target="_blank" rel="noreferrer" class="btn btn-secondary">Ver sitio publico</a>
    </header>

    <nav class="card p-2 mb-6 flex flex-wrap gap-2">
      <router-link
        v-for="item in tabs"
        :key="item.to"
        :to="item.to"
        class="px-3 py-2 rounded-lg text-sm font-medium transition"
        :class="route.path === item.to ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]' : 'hover:bg-[var(--color-app-bg)]'"
      >
        {{ item.label }}
      </router-link>
    </nav>

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();

const tabs = [
  { to: '/admin/landing/inicio', label: 'Inicio' },
  { to: '/admin/landing/pilares', label: 'Pilares' },
  { to: '/admin/landing/quienes-somos', label: 'Quienes somos' },
  { to: '/admin/landing/ecos', label: 'Ecos' },
];
</script>
