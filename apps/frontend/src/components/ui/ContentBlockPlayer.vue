<script setup lang="ts">
/**
 * Renders a single content block of a Topic (video/audio/pdf/imagen/texto).
 *
 * Mirrors the per-kind media logic that used to live in LearningPlayer.vue
 * (play-token fetch, blob vs stream URL, heartbeats) but scoped to ONE block.
 * The parent (LearningPlayer) renders one of these per block via v-for, keyed
 * by block.id — so mount/unmount IS the block-change lifecycle; no internal
 * watch on the block prop is needed.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import * as pdfjsLib from 'pdfjs-dist';
import type { PDFDocumentProxy } from 'pdfjs-dist';
import PdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { apiPost, mediaFetch } from '@/lib/api';
import { sanitizeHtml } from '@/lib/sanitize';
import type { ContentBlockView } from '@/services/courses.service';

pdfjsLib.GlobalWorkerOptions.workerSrc = PdfWorker;

const props = defineProps<{
  temaId: string;
  block: ContentBlockView;
}>();

const emit = defineEmits<{
  progress: [
    payload:
      | { blockId: string; kind: 'video' | 'audio'; videoMaxSeenPct: number; completed: boolean }
      | { blockId: string; kind: 'pdf'; pdfLastPage: number; pdfTotalPages: number; completed: boolean },
  ];
}>();

// Video/audio direct stream URL (native HTTP Range Requests, no blob).
const mediaStreamUrl = ref<string | null>(null);
// PDF/image: fetched as Blob.
const mediaBlobUrl = ref<string | null>(null);
const mediaError = ref('');
const loadingToken = ref(false);

const videoEl = ref<HTMLMediaElement | null>(null);
const playing = ref(false);
const videoBuffering = ref(false);
const videoCurrentTime = ref(props.block.progress?.video_last_pos_seconds || 0);
const videoMaxSeenPct = ref(props.block.progress?.video_max_seen_pct || 0);
const actualDuration = ref<number | null>(null);
const blockCompleted = ref(!!props.block.progress?.completed);

// PDF viewer state.
const pdfContainerEl = ref<HTMLDivElement | null>(null);
const pdfPageEls = ref<(HTMLCanvasElement | null)[]>([]);
const pdfTotalPages = ref(props.block.progress?.pdf_total_pages || 0);
const maxPageSeen = ref(props.block.progress?.pdf_last_page || 1);
const pdfLoading = ref(false);
let pdfDoc: PDFDocumentProxy | null = null;
let pdfLoadingTask: ReturnType<typeof pdfjsLib.getDocument> | null = null;
let pdfObserver: IntersectionObserver | null = null;
const seenPages = new Set<number>();

const kind = computed(() => props.block.kind);
const fallbackDuration = computed(() => props.block.duration_seconds || 180);
const videoDuration = computed(() => actualDuration.value || fallbackDuration.value || 0);

let heartbeatInterval: ReturnType<typeof setInterval> | undefined;

function formatTime(secs: number): string {
  if (isNaN(secs) || secs < 0) return '0:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function emitProgress(): void {
  if (kind.value === 'video' || kind.value === 'audio') {
    emit('progress', {
      blockId: props.block.id,
      kind: kind.value,
      videoMaxSeenPct: videoMaxSeenPct.value,
      completed: blockCompleted.value,
    });
  }
}

function emitPdfProgress(): void {
  emit('progress', {
    blockId: props.block.id,
    kind: 'pdf',
    pdfLastPage: maxPageSeen.value,
    pdfTotalPages: pdfTotalPages.value,
    completed: pdfTotalPages.value > 0 && maxPageSeen.value >= pdfTotalPages.value,
  });
}

async function sendHeartbeat(body: Record<string, unknown>): Promise<void> {
  try {
    await apiPost(`/api/v1/topics/${props.temaId}/heartbeat` as any, {
      body: { type: props.block.kind, block_id: props.block.id, ...body },
    });
  } catch (e) {
    console.error('Block heartbeat failed', e);
  }
}

async function loadMedia(): Promise<void> {
  if (kind.value === 'texto' || !props.block.media_key) return;
  loadingToken.value = true;
  try {
    const tokenResp = (await apiPost('/api/v1/media/play-token' as any, {
      body: { block_id: props.block.id },
    })) as any;

    if (kind.value === 'video' || kind.value === 'audio') {
      // Direct stream URL with token in query so the browser can issue
      // native HTTP Range Requests — true progressive streaming.
      mediaStreamUrl.value = `${tokenResp.media_url}?token=${encodeURIComponent(tokenResp.token)}`;
    } else if (kind.value === 'pdf') {
      const blob = await mediaFetch(tokenResp.media_url, tokenResp.token);
      const arrayBuffer = await blob.arrayBuffer();
      // Release the generic "loadingToken" gate now so the pdf branch of the
      // template mounts (and its canvas refs become available) before we
      // start rendering pages — pdfLoading drives the pdf-local spinner.
      loadingToken.value = false;
      await loadPdf(arrayBuffer);
      return;
    } else {
      // Image: small file, fetched as Blob via Bearer auth.
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

async function loadPdf(data: ArrayBuffer): Promise<void> {
  pdfLoading.value = true;
  try {
    pdfLoadingTask = pdfjsLib.getDocument({ data });
    pdfDoc = await pdfLoadingTask.promise;
    pdfTotalPages.value = pdfDoc.numPages;
    if (maxPageSeen.value > pdfTotalPages.value) maxPageSeen.value = pdfTotalPages.value;

    await nextTick(); // ensure v-else-if branch (kind === 'pdf') has mounted the container
    pdfPageEls.value = new Array<HTMLCanvasElement | null>(pdfDoc.numPages).fill(null);
    await nextTick();

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
      const page = await pdfDoc.getPage(pageNum);
      const viewport = page.getViewport({ scale: 1 });
      const canvas = pdfPageEls.value[pageNum - 1];
      if (!canvas) continue;
      canvas.width = Math.floor(viewport.width * dpr);
      canvas.height = Math.floor(viewport.height * dpr);
      canvas.style.width = '100%';
      canvas.style.aspectRatio = `${viewport.width} / ${viewport.height}`;
      const ctx = canvas.getContext('2d');
      if (!ctx) continue;
      await page.render({
        canvas,
        canvasContext: ctx,
        viewport: page.getViewport({ scale: dpr }),
      }).promise;
    }

    setupPdfObserver();

    // Initial heartbeat once total_pages is known.
    await sendHeartbeat({ last_page: maxPageSeen.value, total_pages: pdfTotalPages.value });
    emitPdfProgress();
  } catch (err: any) {
    console.error('Error rendering PDF:', err);
    mediaError.value = 'No se pudo cargar el documento PDF.';
  } finally {
    pdfLoading.value = false;
  }
}

function setupPdfObserver(): void {
  if (!pdfContainerEl.value) return;
  pdfObserver = new IntersectionObserver(
    (entries) => {
      let advanced = false;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const pageNum = Number((entry.target as HTMLElement).dataset.pageNum);
        if (!pageNum || seenPages.has(pageNum)) continue;
        seenPages.add(pageNum);
        if (pageNum > maxPageSeen.value) {
          maxPageSeen.value = pageNum;
          advanced = true;
        }
      }
      if (advanced) {
        void sendHeartbeat({ last_page: maxPageSeen.value, total_pages: pdfTotalPages.value });
        emitPdfProgress();
      }
    },
    { root: pdfContainerEl.value, threshold: 0.5 },
  );
  for (const canvas of pdfPageEls.value) {
    if (canvas) pdfObserver.observe(canvas);
  }
}

function setPdfCanvasRef(el: unknown, i: number): void {
  pdfPageEls.value[i] = el as HTMLCanvasElement | null;
}

function cleanupPdf(): void {
  if (pdfObserver) {
    pdfObserver.disconnect();
    pdfObserver = null;
  }
  if (pdfLoadingTask) {
    void pdfLoadingTask.destroy();
    pdfLoadingTask = null;
  }
  pdfDoc = null;
  pdfPageEls.value = [];
  seenPages.clear();
}

function toggleVideoPlayback(): void {
  if (!videoEl.value) return;
  if (playing.value) videoEl.value.pause();
  else videoEl.value.play();
}

function onVideoPlay(): void {
  playing.value = true;
  videoBuffering.value = false;
}
function onVideoWaiting(): void {
  videoBuffering.value = true;
}
function onVideoCanPlay(): void {
  videoBuffering.value = false;
}
function onVideoPause(): void {
  playing.value = false;
}

function onLoadedMetadata(): void {
  if (!videoEl.value) return;
  actualDuration.value = videoEl.value.duration;
  // Seek after duration is known, to avoid spurious timeupdate/95% triggers.
  if (videoCurrentTime.value > 0) {
    videoEl.value.currentTime = videoCurrentTime.value;
  }
}

function onVideoTimeUpdate(): void {
  if (!videoEl.value || !actualDuration.value || actualDuration.value <= 0) return;
  videoCurrentTime.value = videoEl.value.currentTime;
  const pct = Math.round((videoEl.value.currentTime / videoDuration.value) * 100);
  if (pct > videoMaxSeenPct.value) {
    videoMaxSeenPct.value = pct;
    if (pct >= 95) blockCompleted.value = true;
    emitProgress();
  }
}

async function onVideoEnded(): Promise<void> {
  playing.value = false;
  if (!videoEl.value || !actualDuration.value) return;
  videoMaxSeenPct.value = 100;
  blockCompleted.value = true;
  await sendHeartbeat({
    pos_seconds: Math.floor(videoEl.value.currentTime),
    duration_seconds: Math.round(videoDuration.value),
    max_seen_pct: 100,
  });
  emitProgress();
}

function startHeartbeatLoop(): void {
  heartbeatInterval = setInterval(async () => {
    if (!playing.value || !videoEl.value || !actualDuration.value || actualDuration.value <= 0) return;
    const pos = Math.floor(videoEl.value.currentTime);
    const pct = Math.max(videoMaxSeenPct.value, Math.round((pos / videoDuration.value) * 100));
    await sendHeartbeat({
      pos_seconds: pos,
      duration_seconds: Math.round(videoDuration.value),
      max_seen_pct: Math.min(100, pct),
    });
    if (pct > videoMaxSeenPct.value) {
      videoMaxSeenPct.value = Math.min(100, pct);
      if (videoMaxSeenPct.value >= 95) blockCompleted.value = true;
      emitProgress();
    }
  }, 5000);
}

function revokeBlob(): void {
  if (mediaBlobUrl.value) {
    URL.revokeObjectURL(mediaBlobUrl.value);
    mediaBlobUrl.value = null;
  }
}

onMounted(async () => {
  await loadMedia();
  if (kind.value === 'video' || kind.value === 'audio') {
    startHeartbeatLoop();
  }
  // Initial emit so the parent's completion map has an entry for this block
  // even before any playback happens.
  emitProgress();
});

onBeforeUnmount(() => {
  revokeBlob();
  cleanupPdf();
  if (heartbeatInterval) clearInterval(heartbeatInterval);
});
</script>

<template>
  <div>
    <div
      v-if="mediaError"
      class="rounded-xl px-4 py-3 text-sm border flex gap-3 items-start bg-red-50 border-red-200 text-red-800 mb-4"
      role="alert"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="shrink-0 mt-0.5"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
      <span>{{ mediaError }}</span>
    </div>

    <div v-else-if="loadingToken" class="card overflow-hidden animate-pulse">
      <div class="aspect-video bg-[var(--color-app-bg)]"></div>
    </div>

    <!-- VIDEO -->
    <div v-else-if="kind === 'video'" class="card overflow-hidden">
      <div class="bg-black relative aspect-video">
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
          @waiting="onVideoWaiting"
          @stalled="onVideoWaiting"
          @canplay="onVideoCanPlay"
          @canplaythrough="onVideoCanPlay"
          preload="metadata"
          playsinline
          controlsList="nodownload"
        />

        <Transition name="fade-fast">
          <div v-if="videoBuffering" class="absolute inset-0 grid place-items-center bg-black/50 z-10 pointer-events-none">
            <div class="w-12 h-12 rounded-full border-4 border-white/20 border-t-white animate-spin"></div>
          </div>
        </Transition>

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
              <div class="h-full bg-white transition-all" :style="{ width: videoMaxSeenPct + '%' }"></div>
            </div>
            <span>{{ formatTime(videoDuration) }}</span>
          </div>
        </div>
      </div>
      <div class="p-4 text-sm text-[var(--color-text-muted)] flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
        Ve el video completo para desbloquear el siguiente paso. ({{ videoMaxSeenPct }}% / 95%)
      </div>
    </div>

    <!-- AUDIO -->
    <div v-else-if="kind === 'audio'" class="card p-6">
      <div class="flex items-center gap-3 mb-4">
        <span class="w-12 h-12 rounded-full bg-[var(--color-primary)]/10 grid place-items-center text-[var(--color-primary)] shrink-0">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
        </span>
        <div class="min-w-0">
          <p class="font-medium truncate">Audio</p>
          <p class="text-xs text-[var(--color-text-muted)]">{{ formatTime(videoDuration) }}</p>
        </div>
      </div>
      <audio
        ref="videoEl"
        class="w-full"
        controls
        controlsList="nodownload"
        crossorigin="anonymous"
        :src="mediaStreamUrl ?? undefined"
        preload="metadata"
        @loadedmetadata="onLoadedMetadata"
        @play="onVideoPlay"
        @pause="onVideoPause"
        @timeupdate="onVideoTimeUpdate"
        @ended="onVideoEnded"
      />
    </div>

    <!-- PDF -->
    <div v-else-if="kind === 'pdf'" class="card overflow-hidden">
      <div
        ref="pdfContainerEl"
        class="w-full max-h-[80vh] overflow-y-auto bg-[var(--color-app-bg)] p-2 sm:p-4 flex flex-col items-center gap-3"
      >
        <canvas
          v-for="(_, i) in pdfPageEls"
          :key="i"
          :ref="(el) => setPdfCanvasRef(el, i)"
          :data-page-num="i + 1"
          class="max-w-full shadow-sm rounded bg-white"
        />
      </div>
      <div v-if="pdfLoading" class="aspect-[3/4] grid place-items-center text-[var(--color-text-muted)] p-6">
        <div class="text-center">
          <div class="w-10 h-10 mx-auto mb-2 rounded-full border-4 border-[var(--color-border)] border-t-[var(--color-primary)] animate-spin"></div>
          <p>Cargando documento...</p>
        </div>
      </div>
      <div class="p-4 text-sm text-[var(--color-text-muted)] flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
        <span v-if="pdfTotalPages > 0">Recorre todo el documento para desbloquear el siguiente paso. (pág. {{ maxPageSeen }}/{{ pdfTotalPages }})</span>
      </div>
    </div>

    <!-- IMAGEN -->
    <div v-else-if="kind === 'imagen'" class="card p-6">
      <img v-if="mediaBlobUrl" :src="mediaBlobUrl" alt="Infografía del tema" class="w-full rounded-lg" loading="lazy" />
      <div v-else class="aspect-[4/3] bg-[var(--color-app-bg)] grid place-items-center rounded-lg text-[var(--color-text-muted)]">
        Cargando imagen...
      </div>
    </div>

    <!-- TEXTO -->
    <div v-else class="card p-6 sm:p-8">
      <div class="prose max-w-none" v-html="sanitizeHtml(block.content_body)"></div>
    </div>
  </div>
</template>

<style scoped>
.fade-fast-enter-active,
.fade-fast-leave-active {
  transition: opacity 0.15s ease;
}
.fade-fast-enter-from,
.fade-fast-leave-to {
  opacity: 0;
}
</style>
