<template>
  <div class="animate-pulse flex flex-col w-full" :class="gapClass">
    <div v-if="hasTitle" class="h-6 bg-[var(--color-border)] rounded-md opacity-50 mb-4" :style="{ width: titleWidth }"></div>
    <div v-for="i in lines" :key="i" class="h-3 bg-[var(--color-border)] rounded-md opacity-30" :style="{ width: getLineWidth(i) }"></div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  lines: { type: Number, default: 3 },
  hasTitle: { type: Boolean, default: false },
  titleWidth: { type: String, default: '40%' },
  gapClass: { type: String, default: 'gap-2' }
})

const getLineWidth = (index: number) => {
  if (index === props.lines) return '60%'; // Last line shorter
  if (index % 2 === 0) return '95%';
  return '100%';
}
</script>
