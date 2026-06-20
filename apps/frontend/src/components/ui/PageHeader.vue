<script setup lang="ts">
interface Props {
  eyebrow?: string;
  title: string;
  subtitle?: string;
}
defineProps<Props>();
</script>

<template>
  <header class="mb-6">
    <p v-if="eyebrow" class="text-[var(--color-primary)] font-medium text-sm mb-1">{{ eyebrow }}</p>
    <h1 class="text-3xl sm:text-4xl font-bold tracking-tight">{{ title }}</h1>
    <p v-if="subtitle" class="text-[var(--color-text-muted)] mt-2 text-base sm:text-lg">{{ subtitle }}</p>
  </header>
</template>
