<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  block?: boolean;
  disabled?: boolean;
  type?: 'button' | 'submit';
}>();
</script>

<template>
  <button
    :type="type ?? 'button'"
    :disabled="disabled"
    :class="[
      'btn',
      variant === 'secondary' ? 'btn-secondary' :
      variant === 'ghost' ? 'btn-ghost' :
      variant === 'danger' ? 'btn-danger' : 'btn-primary',
      block && 'btn-block'
    ]"
  >
    <slot />
  </button>
</template>
