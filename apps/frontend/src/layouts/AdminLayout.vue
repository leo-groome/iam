<template>
  <div class="min-h-screen bg-[var(--color-app-bg)] text-[var(--color-text)]">
    <div class="flex min-h-screen">
      <!-- Desktop Sidebar -->
      <aside class="hidden lg:flex w-[260px] bg-[var(--color-surface)] border-r border-[var(--color-border)] flex-col shadow-sm">
        <div class="px-6 py-8 border-b border-[var(--color-border)] flex flex-col items-center">
          <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-12 w-auto mb-3" />
          <p class="text-[11px] font-bold tracking-widest uppercase text-[var(--color-text-muted)] bg-[var(--color-app-bg)] px-3 py-1 rounded-full border border-[var(--color-border)]">Portal Admin</p>
        </div>
        
        <nav class="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          <div class="px-3 pb-2 text-xs font-bold uppercase text-[var(--color-text-muted)] tracking-wider mt-4 first:mt-0">Principal</div>
          
          <router-link
            v-for="item in nav.slice(0, 3)"
            :key="item.key"
            :to="item.href"
            class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group"
            :class="isActive(item.href) ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)] shadow-sm' : 'text-[var(--color-text)] hover:bg-[var(--color-app-bg)] hover:text-[var(--color-primary)]'"
          >
            <svg class="w-5 h-5 transition-transform duration-200 group-hover:scale-110" :class="isActive(item.href) ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.icon"></path>
            </svg>
            {{ item.label }}
          </router-link>

          <div class="px-3 pb-2 text-xs font-bold uppercase text-[var(--color-text-muted)] tracking-wider mt-8">Gestión & Sistema</div>
          
          <router-link
            v-for="item in nav.slice(3)"
            :key="item.key"
            :to="item.href"
            class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group"
            :class="isActive(item.href) ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)] shadow-sm' : 'text-[var(--color-text)] hover:bg-[var(--color-app-bg)] hover:text-[var(--color-primary)]'"
          >
            <svg class="w-5 h-5 transition-transform duration-200 group-hover:scale-110" :class="isActive(item.href) ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.icon"></path>
            </svg>
            {{ item.label }}
          </router-link>
        </nav>

        <div class="p-4 border-t border-[var(--color-border)] bg-[var(--color-app-bg)]/50">
          <router-link to="/login" class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-[var(--color-text-muted)] hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-200 group">
            <svg class="w-5 h-5 opacity-70 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
            Cerrar sesión
          </router-link>
        </div>
      </aside>

      <!-- Main Content Area -->
      <div class="flex-1 min-w-0 flex flex-col">
        <!-- Mobile Header -->
        <header class="lg:hidden bg-[var(--color-surface)] border-b border-[var(--color-border)] px-4 py-3 flex items-center justify-between sticky top-0 z-20">
          <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-8 w-auto" />
          <router-link to="/admin" class="text-sm text-[var(--color-primary)] font-bold bg-[var(--color-primary-soft)] px-3 py-1.5 rounded-lg">Menú Admin</router-link>
        </header>

        <!-- Dynamic View -->
        <main class="p-6 lg:p-10 max-w-[1400px] w-full mx-auto flex-1">
          <slot />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();

const nav = [
  { href: "/admin", label: "Dashboard", key: "dashboard", icon: "M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" },
  { href: "/admin/cursos", label: "Cursos", key: "cursos", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
  { href: "/admin/estudiantes", label: "Estudiantes", key: "estudiantes", icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" },
  { href: "/admin/landing", label: "Página web", key: "landing", icon: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" },
  { href: "/admin/reportes", label: "Reportes", key: "reportes", icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { href: "/admin/configuracion", label: "Configuración", key: "configuracion", icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" },
];

const isActive = (href: string) => {
  if (href === '/admin') return route.path === '/admin';
  return route.path.startsWith(href);
};
</script>
