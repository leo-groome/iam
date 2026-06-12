<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  type: 'video' | 'pdf' | 'imagen' | 'texto';
  examUrl: string;
  nextUrl?: string;
  hasExam: boolean;
}>();

const progress = ref(0);
const playing = ref(false);
const duration = 180; // mock 3 min
const currentTime = ref(0);
let timer: number | undefined;

const videoWrap = ref<HTMLElement | null>(null);
const isFullscreen = ref(false);

function toggleFullscreen() {
  const el = videoWrap.value;
  if (!el) return;
  if (!document.fullscreenElement) {
    el.requestFullscreen?.().catch(() => {});
  } else {
    document.exitFullscreen?.().catch(() => {});
  }
}

function onFsChange() {
  isFullscreen.value = !!document.fullscreenElement;
}

onMounted(() => {
  document.addEventListener('fullscreenchange', onFsChange);
});
onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFsChange);
  if (timer) clearInterval(timer);
});

const canContinue = computed(() => progress.value >= 95);
const buttonLabel = computed(() => {
  if (!canContinue.value) return progress.value > 0 ? 'Sigue viendo...' : 'Comenzar';
  return props.hasExam ? 'Hacer cuestionario' : 'Siguiente tema';
});
const buttonHref = computed(() => props.hasExam ? props.examUrl : (props.nextUrl ?? '#'));

function togglePlay() {
  if (canContinue.value && props.type === 'video') return;
  playing.value = !playing.value;
  if (playing.value && props.type === 'video') {
    timer = window.setInterval(() => {
      currentTime.value += 1;
      progress.value = Math.min(100, Math.round((currentTime.value / duration) * 100));
      if (progress.value >= 100) {
        playing.value = false;
        clearInterval(timer);
      }
    }, 100);
  } else {
    clearInterval(timer);
  }
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}:${r.toString().padStart(2, '0')}`;
}

onMounted(() => {
  if (props.type !== 'video') {
    window.addEventListener('scroll', () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      progress.value = h > 0 ? Math.min(100, Math.round((window.scrollY / h) * 100)) : 100;
    });
  }
});
</script>

<template>
  <div>
    <div v-if="type === 'video'" class="card overflow-hidden mb-6">
      <div
        ref="videoWrap"
        :class="[
          'bg-[var(--color-text)] relative grid place-items-center',
          isFullscreen ? 'w-screen h-screen' : 'aspect-video'
        ]"
      >
        <button
          @click="togglePlay"
          class="w-20 h-20 rounded-full bg-white/95 grid place-items-center text-[var(--color-primary)] shadow-2xl hover:scale-105 transition"
          :aria-label="playing ? 'Pausar' : 'Reproducir'"
        >
          <svg v-if="!playing" width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>
        </button>
        <div class="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/70 to-transparent">
          <div class="flex items-center gap-3 text-white text-xs">
            <span>{{ formatTime(currentTime) }}</span>
            <div class="flex-1 h-1.5 bg-white/20 rounded-full overflow-hidden">
              <div class="h-full bg-white transition-all" :style="{ width: progress + '%' }"></div>
            </div>
            <span>{{ formatTime(duration) }}</span>
            <button
              @click.stop="toggleFullscreen"
              class="text-white/90 hover:text-white p-1.5 rounded-md hover:bg-white/10 transition"
              :aria-label="isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'"
              :title="isFullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'"
            >
              <svg v-if="!isFullscreen" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3"/><path d="M21 8h-3a2 2 0 0 1-2-2V3"/><path d="M3 16h3a2 2 0 0 1 2 2v3"/><path d="M16 21v-3a2 2 0 0 1 2-2h3"/></svg>
            </button>
          </div>
        </div>
      </div>
      <div class="p-4 text-sm text-[var(--color-text-muted)] flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
        Ve el video completo. No puedes adelantar.
      </div>
    </div>

    <div v-else-if="type === 'pdf'" class="card p-6 mb-6 prose max-w-none">
      <div class="aspect-[3/4] bg-[var(--color-app-bg)] grid place-items-center rounded-lg text-[var(--color-text-muted)]">
        <div class="text-center">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="mx-auto mb-2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
          <p>Visor de PDF</p>
        </div>
      </div>
    </div>

    <div v-else-if="type === 'imagen'" class="card p-6 mb-6">
      <div class="aspect-[4/3] bg-[var(--color-app-bg)] grid place-items-center rounded-lg text-[var(--color-text-muted)]">
        Infografía
      </div>
    </div>

    <article v-else class="card p-6 sm:p-8 mb-6 prose max-w-none">
      <slot />
    </article>

    <div class="fixed bottom-0 left-0 right-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-4 z-20">
      <div class="max-w-3xl mx-auto">
        <a
          :href="canContinue ? buttonHref : undefined"
          :class="['btn btn-block', canContinue ? 'btn-primary' : 'btn-primary opacity-50 pointer-events-none']"
        >
          {{ buttonLabel }}
        </a>
      </div>
    </div>
  </div>
</template>
