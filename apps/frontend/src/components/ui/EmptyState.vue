<script setup lang="ts">
interface Props {
  title: string;
  description?: string;
  ctaLabel?: string;
  ctaHref?: string;
}
defineProps<Props>();
</script>

<template>
  <div class="card p-10 text-center">
    <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--color-primary-soft)] grid place-items-center text-[var(--color-primary)]">
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>
    </div>
    <h3 class="font-bold text-lg mb-1">{{ title }}</h3>
    <p v-if="description" class="text-[var(--color-text-muted)] text-sm max-w-md mx-auto">{{ description }}</p>
    <router-link v-if="ctaLabel && ctaHref" :to="ctaHref" class="btn btn-primary mt-5 inline-flex">{{ ctaLabel }}</router-link>
  </div>
</template>
