<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { apiPost, mediaFetch } from '@/lib/api';

const props = defineProps<{
  tema?: {
    id: string;
    title: string;
    content_type: string;
    content_body?: string;
    duration_seconds?: number;
    media_key?: string;
    has_exam?: boolean;
    state?: string;
    progress?: {
      video_last_pos_seconds: number;
      video_max_seen_pct: number;
      pdf_last_page: number;
      pdf_total_pages: number | null;
    };
  };
  examUrl: string;
  nextUrl?: string;
  hasExam: boolean;
}>();

// Refs and states
const progress = ref(0);
const playing = ref(false);
const videoWrap = ref<HTMLElement | null>(null);
const isFullscreen = ref(false);

const videoEl = ref<HTMLVideoElement | null>(null);
const videoCurrentTime = ref(0);
const videoProgress = ref(0);
const actualDuration = ref<number | null>(null);

// Video: direct stream URL (no Blob — enables native HTTP Range Requests)
const mediaStreamUrl = ref<string | null>(null);
// PDF / image: still fetched as Blob (small files, no seek needed)
const mediaBlobUrl = ref<string | null>(null);
const mediaError = ref('');
const loadingToken = ref(false);
const contentDone = ref(false);
const markingDone = ref(false);

const contentType = computed(() => props.tema?.content_type || 'video');
const duration = computed(() => props.tema?.duration_seconds || 180);
const videoDuration = computed(() => actualDuration.value || duration.value || 0);

let heartbeatInterval: any;
let timer: any;
let scrollHandler: (() => void) | undefined;

// Format seconds to MM:SS
function formatTime(secs: number): string {
  if (isNaN(secs) || secs < 0) return '0:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

// Fullscreen
function toggleFullscreen() {
  const el = videoWrap.value;
  if (!el) return;
  if (!document.fullscreenElement) {
    el.requestFullscreen?.().catch(() => {});
  } else {
    document.exitFullscreen?.().catch(() => {});
  }
}

function onFsChange(): void {
  isFullscreen.value = !!document.fullscreenElement;
}

// Watch for theme changes
watch(
  () => props.tema,
  async (newTema) => {
    // Revoke previous Blob URL if any (PDF/image)
    if (mediaBlobUrl.value) {
      URL.revokeObjectURL(mediaBlobUrl.value);
      mediaBlobUrl.value = null;
    }
    // Clear video stream URL
    mediaStreamUrl.value = null;

    mediaError.value = '';
    loadingToken.value = false;
    playing.value = false;
    videoCurrentTime.value = 0;
    videoProgress.value = 0;
    actualDuration.value = null;
    progress.value = 0;
    contentDone.value = false;
    markingDone.value = false;

    if (heartbeatInterval) clearInterval(heartbeatInterval);
    if (timer) clearInterval(timer);
    if (scrollHandler) {
      window.removeEventListener('scroll', scrollHandler);
      scrollHandler = undefined;
    }

    if (!newTema) return;

    // Load initial progress
    if (newTema.progress && newTema.state) {
      if (['contenido_visto', 'aprobado', 'en_repaso'].includes(newTema.state)) {
        contentDone.value = true;
      }
      if (newTema.content_type === 'video') {
        videoCurrentTime.value = newTema.progress.video_last_pos_seconds || 0;
        videoProgress.value = newTema.progress.video_max_seen_pct || 0;
      }
    }

    // Load private media if needed
    if (newTema.content_type !== 'texto' && newTema.media_key) {
      loadingToken.value = true;
      try {
        const tokenResp = (await apiPost('/api/v1/media/play-token' as any, {
          body: { topic_id: newTema.id },
        })) as any;

        if (newTema.content_type === 'video') {
          // VIDEO: construct direct Worker URL with token in query param.
          // This lets the browser issue native HTTP Range Requests (206 Partial Content)
          // for true progressive streaming — no full download, no RAM spike.
          mediaStreamUrl.value = `${tokenResp.media_url}?token=${encodeURIComponent(tokenResp.token)}`;
        } else {
          // PDF / IMAGE: fetch as Blob (small files, no streaming needed)
          const blob = await mediaFetch(tokenResp.media_url, tokenResp.token);
          mediaBlobUrl.value = URL.createObjectURL(blob);
        }
      } catch (err: any) {
        console.error('Error fetching R2 play token/media:', err);
        mediaError.value = err.message || 'No se pudo cargar el archivo multimedia.';
      } finally {
        loadingToken.value = false;
      }
    }

    // Tracking initialization
    if (newTema.content_type === 'texto' || newTema.content_type === 'imagen') {
      try {
        await apiPost(`/api/v1/topics/${newTema.id}/heartbeat` as any, {
          body: { type: newTema.content_type },
        });
      } catch (e) {
        console.error('Initial heartbeat failed', e);
      }
      setupScrollTracking();
    } else if (newTema.content_type === 'pdf') {
      try {
        await apiPost(`/api/v1/topics/${newTema.id}/heartbeat` as any, {
          body: { type: 'pdf', last_page: 1, total_pages: 1 },
        });
        contentDone.value = true;
        await markContentDone();
      } catch (e) {
        console.error('PDF heartbeat failed', e);
      }
    } else if (newTema.content_type === 'video') {
      // Seek to last position when video element is ready
      setTimeout(() => {
        if (videoEl.value && videoCurrentTime.value > 0) {
          videoEl.value.currentTime = videoCurrentTime.value;
        }
      }, 500);

      // Setup periodic heartbeat
      heartbeatInterval = setInterval(async () => {
        if (playing.value && videoEl.value && props.tema) {
          const pos = Math.floor(videoEl.value.currentTime);
          const maxSeen = Math.max(videoProgress.value, Math.round((pos / videoDuration.value) * 100));
          try {
            await apiPost(`/api/v1/topics/${props.tema.id}/heartbeat` as any, {
              body: { type: 'video', pos_seconds: pos, max_seen_pct: maxSeen },
            });
          } catch (e) {
            console.error('Video heartbeat failed', e);
          }
        }
      }, 5000);
    }
  },
  { immediate: true }
);

function setupScrollTracking(): void {
  scrollHandler = () => {
    const h = document.documentElement.scrollHeight - window.innerHeight;
    const pct = h > 0 ? Math.min(100, Math.round((window.scrollY / h) * 100)) : 100;
    progress.value = pct;
    if (pct >= 95 && !contentDone.value) {
      markContentDone();
    }
  };
  window.addEventListener('scroll', scrollHandler, { passive: true });
}

async function markContentDone() {
  if (!props.tema) return;
  markingDone.value = true;
  try {
    await apiPost(`/api/v1/topics/${props.tema.id}/mark-content-done` as any);
    contentDone.value = true;
  } catch (err) {
    console.error('Error marking content done:', err);
  } finally {
    markingDone.value = false;
  }
}

async function onTextMarkDone(): Promise<void> {
  await markContentDone();
}

// Video Playback
function toggleVideoPlayback() {
  if (!videoEl.value) return;
  if (playing.value) {
    videoEl.value.pause();
  } else {
    videoEl.value.play();
  }
}

function onVideoPlay() {
  playing.value = true;
}

function onVideoPause() {
  playing.value = false;
}

function onVideoTimeUpdate() {
  if (!videoEl.value) return;
  videoCurrentTime.value = videoEl.value.currentTime;
  const pct = Math.round((videoEl.value.currentTime / videoDuration.value) * 100);
  videoProgress.value = Math.max(videoProgress.value, pct);

  if (pct >= 95 && !contentDone.value) {
    markContentDone();
  }
}

function onLoadedMetadata() {
  if (videoEl.value) {
    actualDuration.value = videoEl.value.duration;
  }
}

function onVideoEnded() {
  playing.value = false;
  if (!contentDone.value) {
    markContentDone();
  }
}

onMounted(() => {
  document.addEventListener('fullscreenchange', onFsChange);
});

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFsChange);
  // Only revoke Blob URLs (PDF/image) — video uses direct stream URL, no revoke needed
  if (mediaBlobUrl.value) {
    URL.revokeObjectURL(mediaBlobUrl.value);
  }
  if (heartbeatInterval) clearInterval(heartbeatInterval);
  if (timer) clearInterval(timer);
  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler);
  }
});

// Sticky CTA Bar computed options
const canContinue = computed(() => contentDone.value);
const buttonLabel = computed(() => props.tema?.has_exam ? 'Ir al Examen' : 'Siguiente Tema');
const buttonHref = computed(() => props.tema?.has_exam ? props.examUrl : (props.nextUrl || '#'));
</script>

<template>
  <div>
    <!-- Error banner -->
    <div
      v-if="mediaError"
      class="rounded-xl px-4 py-3 text-sm border flex gap-3 items-start bg-red-50 border-red-200 text-red-800 mb-4"
      role="alert"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 mt-0.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
      <span>{{ mediaError }}</span>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loadingToken" class="card overflow-hidden mb-6 animate-pulse">
      <div class="aspect-video bg-[var(--color-app-bg)]"></div>
    </div>

    <!-- VIDEO -->
    <div v-else-if="contentType === 'video'" class="card overflow-hidden mb-6">
      <div
        ref="videoWrap"
        :class="[
          'bg-black relative',
          isFullscreen ? 'w-screen h-screen' : 'aspect-video',
        ]"
      >
        <video
          ref="videoEl"
          class="w-full h-full object-contain"
          :src="mediaStreamUrl ?? undefined"
          crossorigin="anonymous"
          @loadedmetadata="onLoadedMetadata"
          @play="onVideoPlay"
          @pause="onVideoPause"
          @timeupdate="onVideoTimeUpdate"
          @ended="onVideoEnded"
          preload="metadata"
          playsinline
          controlsList="nodownload"
        />

        <!-- Big center play button when paused -->
        <button
          v-if="!playing && mediaStreamUrl"
          @click="toggleVideoPlayback"
          class="absolute inset-0 w-full h-full grid place-items-center bg-black/20 group"
          aria-label="Reproducir"
        >
          <span class="w-20 h-20 rounded-full bg-white/95 grid place-items-center text-[var(--color-primary)] shadow-2xl group-hover:scale-105 transition">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </span>
        </button>

        <!-- Bottom controls bar -->
        <div class="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/70 to-transparent z-15">
          <div class="flex items-center gap-3 text-white text-xs">
            <button
              @click="toggleVideoPlayback"
              class="text-white/90 hover:text-white p-1.5 rounded-md hover:bg-white/10 transition"
              :aria-label="playing ? 'Pausar' : 'Reproducir'"
            >
              <svg v-if="!playing" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>
            </button>
            <span>{{ formatTime(videoCurrentTime) }}</span>
            <div class="flex-1 h-1.5 bg-white/20 rounded-full overflow-hidden">
              <div class="h-full bg-white transition-all" :style="{ width: videoProgress + '%' }"></div>
            </div>
            <span>{{ formatTime(videoDuration) }}</span>
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
        Ve el video completo para desbloquear el siguiente paso.
      </div>
    </div>

    <!-- PDF -->
    <div v-else-if="contentType === 'pdf'" class="card mb-6 overflow-hidden">
      <iframe
        v-if="mediaBlobUrl"
        :src="mediaBlobUrl"
        class="w-full aspect-[3/4] border-0"
        title="Documento PDF"
      />
      <div v-else class="aspect-[3/4] grid place-items-center text-[var(--color-text-muted)] p-6">
        <div class="text-center">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="mx-auto mb-2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
          <p>Cargando documento...</p>
        </div>
      </div>
    </div>

    <!-- IMAGEN -->
    <div v-else-if="contentType === 'imagen'" class="card p-6 mb-6">
      <img
        v-if="mediaBlobUrl"
        :src="mediaBlobUrl"
        alt="Infografía del tema"
        class="w-full rounded-lg"
        loading="lazy"
      />
      <div v-else class="aspect-[4/3] bg-[var(--color-app-bg)] grid place-items-center rounded-lg text-[var(--color-text-muted)]">
        Cargando imagen...
      </div>
    </div>

    <!-- TEXTO -->
    <article v-else class="card p-6 sm:p-8 mb-6 prose max-w-none">
      <slot />
      <div class="mt-8 pt-6 border-t border-[var(--color-border)] not-prose">
        <button
          v-if="!contentDone"
          @click="onTextMarkDone"
          :disabled="markingDone"
          class="btn btn-primary w-full sm:w-auto disabled:opacity-50"
        >
          {{ markingDone ? 'Guardando...' : 'Marcar como leído' }}
        </button>
        <p v-else class="text-sm text-emerald-600 font-medium flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          Contenido completado
        </p>
      </div>
    </article>

    <!-- Sticky CTA bar -->
    <div class="fixed bottom-0 left-0 right-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-4 z-20">
      <div class="max-w-3xl mx-auto">
        <router-link v-if="canContinue" :to="buttonHref" :class="['btn btn-block btn-primary']">
          {{ buttonLabel }}
        </router-link>
        <span v-else :class="['btn btn-block btn-primary opacity-50 pointer-events-none']">
          {{ buttonLabel }}
        </span>
      </div>
    </div>
  </div>
</template>
