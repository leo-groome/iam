<script setup lang="ts">
import { reactive } from 'vue';
import { mediaService } from '@/services/media.service';
import RichTextEditor from '@/components/ui/RichTextEditor.vue';

export type BlockKind = 'video' | 'pdf' | 'imagen' | 'audio' | 'texto';

export interface Block {
  id?: string;
  kind: BlockKind;
  media_key: string | null;
  content_body: string | null;
  duration_seconds: number | null;
  order_index: number;
}

const props = defineProps<{
  modelValue: Block[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: Block[]): void;
}>();

const makeEmptyBlock = (orderIndex: number): Block => ({
  kind: 'video',
  media_key: null,
  content_body: null,
  duration_seconds: null,
  order_index: orderIndex,
});

// Per-block transient upload UI state, keyed by array index (blocks don't
// always have a stable id — new ones don't until saved).
const uploadState = reactive<Record<number, { uploading: boolean; phase: string | null; error: string | null }>>({});

const kindToScope = (kind: BlockKind): 'video' | 'pdf' | 'imagen' | 'audio' => {
  if (kind === 'texto') return 'imagen'; // unreachable for texto blocks, kept for type safety
  return kind;
};

const acceptFor = (kind: BlockKind): string => {
  switch (kind) {
    case 'video':
      return 'video/mp4, video/webm';
    case 'pdf':
      return 'application/pdf';
    case 'audio':
      return 'audio/mpeg';
    case 'imagen':
      return 'image/jpeg, image/png, image/webp';
    default:
      return '';
  }
};

const emitUpdate = (blocks: Block[]) => {
  emit('update:modelValue', blocks);
};

const addBlock = () => {
  const blocks = [...props.modelValue, makeEmptyBlock(props.modelValue.length)];
  emitUpdate(blocks);
};

const removeBlock = (index: number) => {
  const blocks = props.modelValue.filter((_, i) => i !== index);
  blocks.forEach((b, i) => (b.order_index = i));
  delete uploadState[index];
  emitUpdate(blocks);
};

const moveBlock = (index: number, direction: -1 | 1) => {
  const nextIndex = index + direction;
  if (nextIndex < 0 || nextIndex >= props.modelValue.length) return;
  const blocks = [...props.modelValue];
  const [block] = blocks.splice(index, 1);
  blocks.splice(nextIndex, 0, block);
  blocks.forEach((b, i) => (b.order_index = i));
  emitUpdate(blocks);
};

const onKindChange = (index: number, kind: BlockKind) => {
  const blocks = [...props.modelValue];
  const block = { ...blocks[index], kind };
  // Reset fields that don't apply to the new kind.
  if (kind === 'texto') {
    block.media_key = null;
  } else {
    block.content_body = null;
  }
  blocks[index] = block;
  emitUpdate(blocks);
};

const onContentBodyChange = (index: number, html: string) => {
  const blocks = [...props.modelValue];
  blocks[index] = { ...blocks[index], content_body: html };
  emitUpdate(blocks);
};

const clearMediaKey = (index: number) => {
  const blocks = [...props.modelValue];
  blocks[index] = { ...blocks[index], media_key: null };
  emitUpdate(blocks);
};

const handleFileUpload = async (index: number, event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const block = props.modelValue[index];
  const scope = kindToScope(block.kind);

  uploadState[index] = { uploading: true, phase: null, error: null };
  try {
    let durationSeconds = block.duration_seconds;
    if (scope === 'video' || scope === 'audio') {
      const secs = await mediaService.readMediaDuration(file);
      if (secs) durationSeconds = secs;
    }
    const key = await mediaService.uploadFile(file, scope, (phase) => {
      uploadState[index].phase = phase;
    });
    const blocks = [...props.modelValue];
    blocks[index] = { ...blocks[index], media_key: key, duration_seconds: durationSeconds };
    emitUpdate(blocks);
  } catch (err: any) {
    console.error('Error uploading block file:', err);
    uploadState[index].error = 'No se pudo subir el archivo: ' + (err.message || 'Error desconocido');
  } finally {
    uploadState[index].uploading = false;
    uploadState[index].phase = null;
  }
  // allow re-selecting the same file later
  target.value = '';
};

const durationLabel = (seconds: number | null): string | null => {
  if (!seconds || seconds <= 0) return null;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s < 10 ? '0' : ''}${s}`;
};
</script>

<template>
  <div class="space-y-4">
    <div v-if="modelValue.length === 0" class="card p-8 text-center text-[var(--color-text-muted)]">
      No hay bloques todavía. Agrega el primero.
    </div>

    <div v-for="(block, index) in modelValue" :key="block.id ?? `new-${index}`" class="card p-5 space-y-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <label class="label">Bloque {{ index + 1 }}</label>
          <select class="input" :value="block.kind" @change="onKindChange(index, ($event.target as HTMLSelectElement).value as BlockKind)">
            <option value="video">Video</option>
            <option value="pdf">PDF</option>
            <option value="imagen">Imagen / Infografía</option>
            <option value="audio">Audio (MP3)</option>
            <option value="texto">Texto enriquecido</option>
          </select>
        </div>
        <div class="flex gap-2 shrink-0">
          <button type="button" @click="moveBlock(index, -1)" :disabled="index === 0" class="btn btn-secondary px-3">Subir</button>
          <button type="button" @click="moveBlock(index, 1)" :disabled="index === modelValue.length - 1" class="btn btn-secondary px-3">Bajar</button>
          <button type="button" @click="removeBlock(index)" class="btn btn-secondary text-[var(--color-error)]">Eliminar</button>
        </div>
      </div>

      <!-- Media block -->
      <div v-if="block.kind !== 'texto'">
        <p v-if="(block.kind === 'video' || block.kind === 'audio') && durationLabel(block.duration_seconds)" class="text-xs text-[var(--color-text-muted)] mb-2">
          Duración detectada automáticamente: <span class="font-medium">{{ durationLabel(block.duration_seconds) }}</span>
        </p>

        <div v-if="uploadState[index]?.error" class="mb-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          {{ uploadState[index].error }}
        </div>

        <div v-if="block.media_key" class="border border-[var(--color-border)] rounded-xl p-4 flex items-center justify-between bg-[var(--color-bg-hover)]">
          <div class="flex items-center gap-3 overflow-hidden">
            <svg class="w-8 h-8 text-[var(--color-primary)] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            <span class="text-sm font-medium truncate">{{ block.media_key.split('/').pop() || 'Archivo actual' }}</span>
          </div>
          <button type="button" @click="clearMediaKey(index)" class="text-xs text-red-600 hover:bg-red-50 px-2.5 py-1 rounded font-medium border border-red-200">Reemplazar</button>
        </div>
        <div v-else-if="uploadState[index]?.uploading" class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-8 text-center bg-[var(--color-app-bg)] flex flex-col items-center">
          <svg class="animate-spin h-6 w-6 text-[var(--color-primary)] mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <p class="text-sm font-medium text-[var(--color-text)]">{{ uploadState[index].phase === 'optimizing' ? 'Optimizando video para streaming...' : 'Subiendo a Cloudflare R2...' }}</p>
          <p class="text-xs text-[var(--color-text-muted)] mt-1">
            {{ uploadState[index].phase === 'optimizing' ? 'Reordenando metadatos (sin recodificar)' : 'Transfiriendo directamente al CDN' }}
          </p>
        </div>
        <div v-else class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-6 text-center hover:bg-[var(--color-app-bg)] transition-colors relative cursor-pointer group">
          <input
            type="file"
            :accept="acceptFor(block.kind)"
            @change="handleFileUpload(index, $event)"
            class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          />
          <div class="space-y-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="text-sm text-[var(--color-text-muted)]">Arrastra o haz clic para subir</p>
            <p class="text-xs text-[var(--color-text-muted)]">
              {{ block.kind === 'video' ? 'Video (mp4/webm, máx 500 MB)' : (block.kind === 'pdf' ? 'Documento PDF (máx 50 MB)' : (block.kind === 'audio' ? 'Audio (mp3, máx 50 MB)' : 'Imagen (jpeg/png/webp, máx 10 MB)')) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Text block -->
      <div v-else>
        <label class="label">Contenido</label>
        <RichTextEditor :model-value="block.content_body || ''" @update:model-value="(html) => onContentBodyChange(index, html)" />
        <p v-if="!block.content_body || !block.content_body.trim()" class="help text-[var(--color-error)]">Este bloque de texto necesita contenido.</p>
      </div>
    </div>

    <button type="button" @click="addBlock" class="btn btn-secondary">+ Agregar bloque</button>
  </div>
</template>
