<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { apiPost, mediaFetch, ApiError } from '@/lib/api'
import type { PlayTokenResponse } from '@/lib/api'

const props = defineProps<{
  topicId: string
  contentType: 'video' | 'pdf' | 'imagen' | 'texto'
  nextUrl?: string
  examUrl?: string
  hasExam: boolean
}>()

// ─── State ────────────────────────────────────────────────────────────────────
const loadingToken = ref(true)
const mediaError = ref<string | null>(null)
const markingDone = ref(false)
const contentDone = ref(false)

const mediaBlobUrl = ref<string | null>(null)
const playToken = ref<PlayTokenResponse | null>(null)
const tokenExpiresAt = ref<number>(0)

const videoEl = ref<HTMLVideoElement | null>(null)
const videoWrap = ref<HTMLElement | null>(null)
const isFullscreen = ref(false)
const playing = ref(false)
const videoProgress = ref(0)

let heartbeatInterval: number | undefined
let scrollHandler: (() => void) | undefined

// ─── Token management ─────────────────────────────────────────────────────────
async function fetchPlayToken(): Promise<PlayTokenResponse> {
  const res = await apiPost('/api/v1/media/play-token', {
    body: { topic_id: props.topicId },
  })
  return res as PlayTokenResponse
}

function isTokenExpired(): boolean {
  return Date.now() >= tokenExpiresAt.value - 30_000
}

async function ensureFreshToken(): Promise<PlayTokenResponse> {
  if (!playToken.value || isTokenExpired()) {
    const fresh = await fetchPlayToken()
    playToken.value = fresh
    tokenExpiresAt.value = Date.now() + fresh.expires_in * 1000
  }
  return playToken.value
}

// ─── Media loading ────────────────────────────────────────────────────────────
async function loadMedia(token: PlayTokenResponse): Promise<void> {
  if (props.contentType === 'texto') return

  let blob: Blob
  try {
    blob = await mediaFetch(token.media_url, token.token)
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      const fresh = await fetchPlayToken()
      playToken.value = fresh
      tokenExpiresAt.value = Date.now() + fresh.expires_in * 1000
      blob = await mediaFetch(fresh.media_url, fresh.token)
    } else {
      throw err
    }
  }

  if (mediaBlobUrl.value) URL.revokeObjectURL(mediaBlobUrl.value)
  mediaBlobUrl.value = URL.createObjectURL(blob)
}

// ─── Mark content done ────────────────────────────────────────────────────────
async function markContentDone(): Promise<void> {
  if (contentDone.value || markingDone.value) return
  markingDone.value = true
  try {
    await apiPost('/api/v1/topics/{topic_id}/mark-content-done', {
      params: { topic_id: props.topicId },
    })
    contentDone.value = true
  } catch (err) {
    if (err instanceof ApiError && (err.status === 403 || err.status === 422)) {
      contentDone.value = true
    } else {
      mediaError.value = err instanceof ApiError ? err.message : 'Error al guardar el progreso'
    }
  } finally {
    markingDone.value = false
  }
}

// ─── Heartbeat ────────────────────────────────────────────────────────────────
function startHeartbeat(): void {
  if (heartbeatInterval) return
  heartbeatInterval = window.setInterval(async () => {
    if (!videoEl.value || videoEl.value.paused) return
    try {
      await apiPost('/api/v1/topics/{topic_id}/heartbeat', {
        params: { topic_id: props.topicId },
      })
    } catch {
      // heartbeat is best-effort
    }
  }, 5000)
}

function stopHeartbeat(): void {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = undefined
  }
}

// ─── Video handlers ───────────────────────────────────────────────────────────
function onVideoPlay(): void {
  playing.value = true
  startHeartbeat()
}

function onVideoPause(): void {
  playing.value = false
  stopHeartbeat()
}

function onVideoTimeUpdate(): void {
  const v = videoEl.value
  if (!v || !v.duration) return
  const pct = Math.min(100, Math.round((v.currentTime / v.duration) * 100))
  videoProgress.value = pct
  if (pct >= 95 && !contentDone.value) markContentDone()
}

function onVideoEnded(): void {
  playing.value = false
  stopHeartbeat()
  videoProgress.value = 100
  if (!contentDone.value) markContentDone()
}

function toggleVideoPlayback(): void {
  if (!videoEl.value) return
  videoEl.value.paused ? videoEl.value.play() : videoEl.value.pause()
}

// ─── Fullscreen ───────────────────────────────────────────────────────────────
function toggleFullscreen(): void {
  const el = videoWrap.value
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen?.().catch(() => {})
  } else {
    document.exitFullscreen?.().catch(() => {})
  }
}

function onFsChange(): void {
  isFullscreen.value = !!document.fullscreenElement
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60)
  const r = Math.floor(s % 60)
  return `${m}:${r.toString().padStart(2, '0')}`
}

// ─── Scroll tracking for non-video ───────────────────────────────────────────
function setupScrollTracking(): void {
  scrollHandler = () => {
    const h = document.documentElement.scrollHeight - window.innerHeight
    const pct = h > 0 ? Math.min(100, Math.round((window.scrollY / h) * 100)) : 100
    if (pct >= 95 && !contentDone.value) markContentDone()
  }
  window.addEventListener('scroll', scrollHandler, { passive: true })
}

// ─── Texto: manual completion ─────────────────────────────────────────────────
async function onTextMarkDone(): Promise<void> {
  await markContentDone()
}

// ─── Derived ──────────────────────────────────────────────────────────────────
const canContinue = computed(() => contentDone.value)

const buttonLabel = computed(() => {
  if (!canContinue.value) return 'Completa el contenido para continuar'
  return props.hasExam ? 'Hacer cuestionario' : 'Siguiente tema'
})

const buttonHref = computed(() =>
  props.hasExam ? (props.examUrl ?? '#') : (props.nextUrl ?? '#'),
)

const videoDuration = computed(() => videoEl.value?.duration ?? 0)
const videoCurrentTime = computed(() => videoEl.value?.currentTime ?? 0)

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  document.addEventListener('fullscreenchange', onFsChange)

  try {
    const token = await fetchPlayToken()
    playToken.value = token
    tokenExpiresAt.value = Date.now() + token.expires_in * 1000
    await loadMedia(token)
  } catch (err) {
    mediaError.value = err instanceof ApiError ? err.message : 'No se pudo cargar el contenido'
  } finally {
    loadingToken.value = false
  }

  if (props.contentType !== 'video') {
    setupScrollTracking()
  }
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', onFsChange)
  stopHeartbeat()
  if (scrollHandler) window.removeEventListener('scroll', scrollHandler)
  if (mediaBlobUrl.value) URL.revokeObjectURL(mediaBlobUrl.value)
})

watch([mediaBlobUrl, videoEl], ([blob, el]) => {
  if (blob && el && el.src !== blob) {
    el.src = blob
  }
})
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
          :src="mediaBlobUrl ?? undefined"
          @play="onVideoPlay"
          @pause="onVideoPause"
          @timeupdate="onVideoTimeUpdate"
          @ended="onVideoEnded"
          preload="metadata"
          playsinline
        />

        <!-- Big center play button when paused -->
        <button
          v-if="!playing && mediaBlobUrl"
          @click="toggleVideoPlayback"
          class="absolute inset-0 w-full h-full grid place-items-center bg-black/20 group"
          aria-label="Reproducir"
        >
          <span class="w-20 h-20 rounded-full bg-white/95 grid place-items-center text-[var(--color-primary)] shadow-2xl group-hover:scale-105 transition">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          </span>
        </button>

        <!-- Bottom controls bar -->
        <div class="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/70 to-transparent">
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
        <a
          :href="canContinue ? buttonHref : undefined"
          :class="[
            'btn btn-block',
            canContinue ? 'btn-primary' : 'btn-primary opacity-50 pointer-events-none',
          ]"
          :aria-disabled="!canContinue"
        >
          {{ buttonLabel }}
        </a>
      </div>
    </div>
  </div>
</template>
