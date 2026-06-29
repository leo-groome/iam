<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden w-full animate-pulse">
    <!-- Header -->
    <div class="bg-[var(--color-bg-hover)] border-b border-[var(--color-border)] p-4 flex gap-4">
      <div v-for="i in columns" :key="'th-'+i" class="h-4 bg-[var(--color-border)] rounded-md opacity-50 flex-1"></div>
    </div>
    <!-- Rows -->
    <div class="divide-y divide-[var(--color-border)]">
      <div v-for="row in rows" :key="'tr-'+row" class="p-4 flex items-center gap-4">
        <!-- Avatar/Icon column (optional, assume first column has it if requested) -->
        <div v-if="hasAvatar" class="w-10 h-10 rounded-full bg-[var(--color-border)] opacity-50 shrink-0"></div>
        <div v-for="col in columns" :key="'td-'+row+'-'+col" class="flex-1 space-y-2">
          <div class="h-3 bg-[var(--color-border)] rounded-md w-3/4 opacity-30"></div>
          <div v-if="col === 1" class="h-2 bg-[var(--color-border)] rounded-md w-1/2 opacity-20"></div>
        </div>
        <!-- Actions column -->
        <div class="w-8 h-8 rounded-md bg-[var(--color-border)] opacity-30 shrink-0"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  rows: { type: Number, default: 5 },
  columns: { type: Number, default: 4 },
  hasAvatar: { type: Boolean, default: true }
})
</script>
