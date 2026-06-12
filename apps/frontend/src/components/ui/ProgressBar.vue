<script setup lang="ts">
const props = defineProps<{ value: number; label?: string; showPercent?: boolean }>();
const safe = () => Math.max(0, Math.min(100, props.value));
</script>

<template>
  <div>
    <div v-if="label || showPercent" class="flex justify-between text-sm text-[var(--color-text-muted)] mb-1.5">
      <span v-if="label">{{ label }}</span>
      <span v-if="showPercent">{{ safe() }}%</span>
    </div>
    <div class="h-2 bg-[var(--color-primary-soft)] rounded-full overflow-hidden">
      <div class="h-full bg-[var(--color-primary)] transition-all duration-500" :style="{ width: safe() + '%' }"></div>
    </div>
  </div>
</template>
