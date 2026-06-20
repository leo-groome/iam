<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  label: string;
  value: string | number;
  delta?: string;
  trend?: 'up' | 'down' | 'neutral';
}
const props = withDefaults(defineProps<Props>(), {
  trend: 'neutral'
});

const trendColor = computed(() => props.trend === 'up' ? 'text-emerald-600' : props.trend === 'down' ? 'text-red-600' : 'text-[var(--color-text-muted)]');
</script>

<template>
  <div class="card p-5">
    <p class="text-sm text-[var(--color-text-muted)]">{{ label }}</p>
    <p class="text-3xl font-bold mt-1">{{ value }}</p>
    <p v-if="delta" :class="`text-xs mt-1 ${trendColor}`">{{ delta }}</p>
  </div>
</template>
