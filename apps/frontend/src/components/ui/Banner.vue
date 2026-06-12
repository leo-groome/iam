<script setup lang="ts">
defineProps<{ kind?: 'info' | 'success' | 'warning' | 'error'; title?: string }>();
</script>

<template>
  <div
    :class="[
      'rounded-xl px-4 py-3 text-sm border flex gap-3 items-start',
      kind === 'success' && 'bg-emerald-50 border-emerald-200 text-emerald-800',
      kind === 'warning' && 'bg-amber-50 border-amber-200 text-amber-800',
      kind === 'error' && 'bg-red-50 border-red-200 text-red-800',
      (!kind || kind === 'info') && 'bg-[var(--color-primary-soft)] border-[var(--color-border)] text-[var(--color-primary)]'
    ]"
  >
    <div class="flex-1">
      <p v-if="title" class="font-semibold mb-0.5">{{ title }}</p>
      <slot />
    </div>
  </div>
</template>
