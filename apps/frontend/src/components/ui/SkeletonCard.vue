<template>
  <div class="card p-6 w-full animate-pulse flex flex-col gap-4">
    <!-- Image placeholder -->
    <div v-if="hasImage" class="w-full h-40 bg-[var(--color-border)] rounded-xl opacity-50"></div>
    
    <div class="flex items-center gap-3">
      <!-- Icon placeholder -->
      <div v-if="hasIcon" class="w-10 h-10 rounded-lg bg-[var(--color-border)] opacity-50 shrink-0"></div>
      
      <!-- Title placeholder -->
      <div class="flex-1 space-y-2">
        <div class="h-5 bg-[var(--color-border)] rounded-md w-3/4 opacity-50"></div>
        <div v-if="hasSubtitle" class="h-3 bg-[var(--color-border)] rounded-md w-1/2 opacity-30"></div>
      </div>
    </div>
    
    <!-- Content lines placeholder -->
    <div class="space-y-2 mt-2">
      <div class="h-3 bg-[var(--color-border)] rounded-md w-full opacity-30"></div>
      <div class="h-3 bg-[var(--color-border)] rounded-md w-5/6 opacity-30"></div>
    </div>
    
    <!-- Footer/Button placeholder -->
    <div v-if="hasFooter" class="mt-auto pt-4 flex justify-between items-center">
      <div class="h-3 bg-[var(--color-border)] rounded-md w-1/4 opacity-30"></div>
      <div class="h-8 bg-[var(--color-border)] rounded-full w-24 opacity-50"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  hasImage: { type: Boolean, default: true },
  hasIcon: { type: Boolean, default: false },
  hasSubtitle: { type: Boolean, default: true },
  hasFooter: { type: Boolean, default: true }
})
</script>
