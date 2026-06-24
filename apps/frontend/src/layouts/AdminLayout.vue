<template>
  <div class="min-h-screen bg-[var(--color-app-bg)] text-[var(--color-text)]">
    <div class="flex min-h-screen">
      <!-- Desktop Sidebar -->
      <aside class="hidden lg:flex w-64 bg-[var(--color-surface)] border-r border-[var(--color-border)] flex-col">
        <div class="px-6 py-5 border-b border-[var(--color-border)]">
          <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-10 w-auto" />
          <p class="text-xs text-[var(--color-text-muted)] mt-2">Panel admin</p>
        </div>
        <nav class="flex-1 p-3 space-y-1">
          <router-link
            v-for="item in nav"
            :key="item.key"
            :to="item.href"
            class="block px-3 py-2.5 rounded-lg text-sm font-medium transition"
            :class="isActive(item.href) ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]' : 'text-[var(--color-text)] hover:bg-[var(--color-app-bg)]'"
          >
            {{ item.label }}
          </router-link>
        </nav>
        <div class="p-4 border-t border-[var(--color-border)]">
          <router-link to="/login" class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
            Cerrar sesión
          </router-link>
        </div>
      </aside>

      <!-- Main Content Area -->
      <div class="flex-1 min-w-0">
        <!-- Mobile Header -->
        <header class="lg:hidden bg-[var(--color-surface)] border-b border-[var(--color-border)] px-4 py-3 flex items-center justify-between">
          <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-8 w-auto" />
          <router-link to="/admin" class="text-sm text-[var(--color-primary)] font-medium">Inicio</router-link>
        </header>

        <!-- Dynamic View -->
        <main class="p-4 lg:p-8 max-w-6xl">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();

const nav = [
  { href: "/admin", label: "Dashboard", key: "dashboard" },
  { href: "/admin/cursos", label: "Cursos", key: "cursos" },
  { href: "/admin/estudiantes", label: "Estudiantes", key: "estudiantes" },
  { href: "/admin/landing", label: "Página web", key: "landing" },
  { href: "/admin/reportes", label: "Reportes", key: "reportes" },
  { href: "/admin/configuracion", label: "Configuración", key: "configuracion" },
];

const isActive = (href: string) => {
  if (href === '/admin') return route.path === '/admin';
  return route.path.startsWith(href);
};
</script>
