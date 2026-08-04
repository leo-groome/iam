<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { apiPost } from '@/lib/api';
import ContentBlockPlayer from '@/components/ui/ContentBlockPlayer.vue';
import type { ContentBlockView } from '@/services/courses.service';

const emit = defineEmits<{ 'content-done': [] }>();

const props = defineProps<{
  tema?: {
    id: string;
    title: string;
    content_type: string;
    has_exam?: boolean;
    state?: string;
    blocks?: ContentBlockView[];
  };
  examUrl: string;
  nextUrl?: string;
  hasExam: boolean;
}>();

const doneStates = ['contenido_visto', 'aprobado'];

const markingDone = ref(false);
const markDoneSuccess = ref(false);
const contentDone = computed(() => !!props.tema?.state && doneStates.includes(props.tema.state));

// Per-block progress, keyed by block id — fed by ContentBlockPlayer's
// @progress event. Video and pdf blocks are "required" and gate class
// completion; other kinds report into this map too (useful for badges) but
// aren't read by allRequiredComplete.
interface BlockProgressEntry {
  videoMaxSeenPct?: number;
  completed: boolean;
  pdfLastPage?: number;
  pdfTotalPages?: number;
}
const blockProgress = reactive<Record<string, BlockProgressEntry>>({});

function onBlockProgress(
  payload:
    | { blockId: string; kind: 'video' | 'audio'; videoMaxSeenPct: number; completed: boolean }
    | { blockId: string; kind: 'pdf'; pdfLastPage: number; pdfTotalPages: number; completed: boolean },
): void {
  if (payload.kind === 'pdf') {
    blockProgress[payload.blockId] = {
      pdfLastPage: payload.pdfLastPage,
      pdfTotalPages: payload.pdfTotalPages,
      completed: payload.completed,
    };
  } else {
    blockProgress[payload.blockId] = {
      videoMaxSeenPct: payload.videoMaxSeenPct,
      completed: payload.completed,
    };
  }
}

const sortedBlocks = computed<ContentBlockView[]>(() => {
  return [...(props.tema?.blocks || [])].sort((a, b) => a.order_index - b.order_index);
});

const videoBlocks = computed(() => sortedBlocks.value.filter((b) => b.kind === 'video'));
const pdfBlocks = computed(() => sortedBlocks.value.filter((b) => b.kind === 'pdf'));
const requiredBlocks = computed(() => sortedBlocks.value.filter((b) => b.kind === 'video' || b.kind === 'pdf'));

function videoPct(b: ContentBlockView): number {
  const live = blockProgress[b.id];
  return live?.videoMaxSeenPct ?? b.progress?.video_max_seen_pct ?? 0;
}

function pdfLastPage(b: ContentBlockView): number {
  const live = blockProgress[b.id];
  return live?.pdfLastPage ?? b.progress?.pdf_last_page ?? 0;
}

function pdfTotalPages(b: ContentBlockView): number {
  const live = blockProgress[b.id];
  return live?.pdfTotalPages ?? b.progress?.pdf_total_pages ?? 0;
}

// Gating rule: no required (video/pdf) blocks → honor system (always
// unlocked). With required blocks, every video must be ≥95% seen and every
// pdf must have last_page ≥ total_pages — matches backend mark-content-done
// semantics exactly.
const allRequiredComplete = computed(() => {
  if (requiredBlocks.value.length === 0) return true;
  const videosOk = videoBlocks.value.every((b) => videoPct(b) >= 95);
  const pdfsOk = pdfBlocks.value.every((b) => {
    const total = pdfTotalPages(b);
    return total > 0 && pdfLastPage(b) >= total;
  });
  return videosOk && pdfsOk;
});

const overallVideoPct = computed(() => {
  if (videoBlocks.value.length === 0) return 100;
  const total = videoBlocks.value.reduce((sum, b) => sum + Math.min(100, videoPct(b)), 0);
  return Math.round(total / videoBlocks.value.length);
});

async function markContentDone(): Promise<void> {
  if (!props.tema || !allRequiredComplete.value || contentDone.value) return;
  markingDone.value = true;
  try {
    await apiPost(`/api/v1/topics/${props.tema.id}/mark-content-done` as any);
    emit('content-done');
    markDoneSuccess.value = true;
    setTimeout(() => {
      markDoneSuccess.value = false;
    }, 2000);
  } catch (err) {
    console.error('Error marking content done:', err);
  } finally {
    markingDone.value = false;
  }
}

const canContinue = computed(() => contentDone.value);
const buttonLabel = computed(() => ((props.tema?.has_exam && props.tema?.state !== 'aprobado') ? 'Ir al Examen' : 'Siguiente Tema'));
const buttonHref = computed(() => ((props.tema?.has_exam && props.tema?.state !== 'aprobado') ? props.examUrl : (props.nextUrl || '#')));

function blockLabel(kind: ContentBlockView['kind']): string {
  switch (kind) {
    case 'video':
      return 'Video';
    case 'audio':
      return 'Audio';
    case 'pdf':
      return 'PDF';
    case 'imagen':
      return 'Imagen';
    default:
      return 'Texto';
  }
}
</script>

<template>
  <div>
    <div v-for="block in sortedBlocks" :key="block.id" class="mb-6">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">{{ blockLabel(block.kind) }}</span>
        <span
          v-if="block.kind === 'video' || block.kind === 'pdf'"
          class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
        >
          Requerido
        </span>
        <span v-else class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-[var(--color-border)] text-[var(--color-text-muted)]">
          Complementario
        </span>
        <span v-if="block.kind === 'pdf' && pdfTotalPages(block) > 0" class="text-[10px] text-[var(--color-text-muted)]">
          pág. {{ Math.min(pdfLastPage(block), pdfTotalPages(block)) }}/{{ pdfTotalPages(block) }}
        </span>
      </div>
      <ContentBlockPlayer :tema-id="tema!.id" :block="block" @progress="onBlockProgress" />
    </div>

    <div v-if="sortedBlocks.length === 0" class="card p-8 text-center text-[var(--color-text-muted)] mb-6">
      Esta clase todavía no tiene contenido publicado.
    </div>

    <!-- Sticky CTA bar -->
    <div class="fixed bottom-0 left-0 right-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] px-4 pt-3 pb-4 z-20">
      <div class="max-w-3xl mx-auto">
        <!-- Video progress bar toward unlock -->
        <div v-if="videoBlocks.length > 0 && !canContinue && !markingDone" class="mb-3">
          <div class="flex justify-between text-xs text-[var(--color-text-muted)] mb-1.5">
            <span>Progreso de video</span>
            <span>{{ overallVideoPct }}%<span class="opacity-60"> / 95% para continuar</span></span>
          </div>
          <div class="h-1 bg-[var(--color-border)] rounded-full overflow-hidden">
            <div
              class="h-full bg-[var(--color-primary)] transition-all duration-500 rounded-full"
              :style="{ width: Math.min(100, (overallVideoPct / 95) * 100) + '%' }"
            ></div>
          </div>
        </div>

        <Transition name="fade-fast">
          <div v-if="markingDone" class="flex items-center justify-center gap-2 text-sm text-[var(--color-text-muted)] mb-2">
            <div class="w-4 h-4 rounded-full border-2 border-[var(--color-primary)]/30 border-t-[var(--color-primary)] animate-spin"></div>
            <span>Registrando progreso...</span>
          </div>
        </Transition>

        <!-- Single CTA slot: "Marcar como completado" until the class is
             done server-side, then it transforms into the next-step link. -->
        <Transition name="cta-unlock" mode="out-in">
          <router-link v-if="canContinue" key="active" :to="buttonHref" class="btn btn-block btn-primary flex items-center justify-center gap-2">
            <Transition name="fade-fast" mode="out-in">
              <svg v-if="markDoneSuccess" key="check" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="shrink-0"><polyline points="20 6 9 17 4 12"/></svg>
            </Transition>
            {{ buttonLabel }}
          </router-link>
          <button
            v-else
            key="mark-done"
            @click="markContentDone"
            :disabled="!allRequiredComplete || markingDone"
            class="btn btn-block btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {{ markingDone ? 'Guardando...' : 'Marcar como completado' }}
          </button>
        </Transition>
      </div>
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

.cta-unlock-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.cta-unlock-leave-active {
  transition: all 0.15s ease;
}
.cta-unlock-enter-from {
  opacity: 0;
  transform: translateY(6px) scale(0.97);
}
.cta-unlock-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
