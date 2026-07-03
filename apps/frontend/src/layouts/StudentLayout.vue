<template>
  <div class="min-h-screen bg-[var(--color-app-bg)] text-[var(--color-text)]">
    <!-- Header -->
    <header
      v-if="showHeader"
      class="sticky top-0 z-40 backdrop-blur-xl bg-[var(--color-surface)]/85 border-b border-[var(--color-border)] print:hidden"
    >
      <div class="w-full pl-5 pr-4 sm:pl-6 sm:pr-6">
        <div class="h-20 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
          <router-link to="/catalogo" class="flex items-center justify-self-start" aria-label="Inicio">
            <img loading="lazy" src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-14 sm:h-16 w-auto" />
          </router-link>

          <nav class="hidden md:flex items-center gap-1 justify-self-center">
            <router-link
              to="/catalogo"
              class="px-4 py-2 rounded-lg text-sm font-medium transition"
              :class="isActive('/catalogo') ? 'text-[var(--color-primary)] bg-[var(--color-primary-soft)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-app-bg)]'"
            >
              Mis cursos
            </router-link>
          </nav>

          <div v-if="authStore.user" class="flex items-center gap-2 justify-self-end">
            <router-link
              to="/perfil"
              title="Mi perfil"
              class="hidden md:flex items-center gap-2 pl-1 pr-1 sm:pr-3 py-1 rounded-full transition"
              :class="isActive('/perfil') ? 'bg-[var(--color-primary-soft)] ring-2 ring-[var(--color-primary)]/30' : 'hover:bg-[var(--color-app-bg)]'"
            >
              <UserAvatar :name="displayName || 'Estudiante'" size="w-9 h-9" />
              <span class="hidden sm:inline text-sm font-medium" :class="{ 'text-[var(--color-primary)]': isActive('/perfil') }">{{ displayName }}</span>
            </router-link>
          </div>
        </div>

        <div v-if="progress !== null && courseName" class="lg:hidden pb-2">
          <div class="flex items-center justify-between text-[11px] text-[var(--color-text-muted)] mb-1.5">
            <span class="truncate font-medium text-[var(--color-text)]">{{ courseName }}</span>
            <span class="ml-2 shrink-0">{{ progress }}%</span>
          </div>
          <div class="h-1 bg-[var(--color-primary-soft)] rounded-full overflow-hidden">
            <div class="h-full bg-[var(--color-primary)] transition-all duration-500" :style="`width: ${progress}%`"></div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main :class="[`mx-auto px-4 py-6 pb-32 print:p-0 print:pb-0`, wide ? 'max-w-6xl' : 'max-w-3xl']">
      <slot />
    </main>

    <!-- Mobile Nav -->
    <nav
      v-if="showHeader"
      class="md:hidden fixed bottom-0 inset-x-0 z-30 bg-[var(--color-surface)]/95 backdrop-blur-xl border-t border-[var(--color-border)] print:hidden"
    >
      <div class="flex justify-around h-16">
        <router-link
          to="/catalogo"
          class="flex flex-col items-center justify-center gap-0.5 flex-1 text-[10px] font-medium"
          :class="isActive('/catalogo') ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
          <span>Inicio</span>
        </router-link>
        <router-link
          to="/perfil"
          class="flex flex-col items-center justify-center gap-0.5 flex-1 text-[10px] font-medium"
          :class="isActive('/perfil') ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span>Perfil</span>
        </router-link>
      </div>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useProgressStore } from '@/stores/progress';
import UserAvatar from '@/components/ui/UserAvatar.vue';

const route = useRoute();
const authStore = useAuthStore();
const progressStore = useProgressStore();

const displayName = computed(() => authStore.user?.full_name ?? '');
const initial = computed(() => displayName.value.charAt(0).toUpperCase() || '·');

// These could eventually be connected to a Pinia store if they need to be dynamically updated by child views
const showHeader = computed(() => route.meta.showHeader !== false);
const wide = computed(() => route.meta.wide === true);
const courseName = computed(() => route.meta.courseName ?? null);
const slug = computed(() => route.params.slug as string | undefined);

const progress = computed(() => {
  if (slug.value && route.path.startsWith('/curso/')) {
    return progressStore.coursePercentage(slug.value);
  }
  return route.meta.progress ?? null;
});

const isActive = (path: string) => {
  if (path === '/catalogo') {
    return route.path === '/catalogo' || route.path.startsWith('/curso/');
  }
  return route.path.startsWith(path);
};
</script>
