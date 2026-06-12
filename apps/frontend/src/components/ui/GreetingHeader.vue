<script setup lang="ts">
import { ref, onMounted } from 'vue';

defineProps<{ name: string }>();

const greeting = ref('Hola');

onMounted(() => {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) greeting.value = 'Buenos días';
  else if (h >= 12 && h < 19) greeting.value = 'Buenas tardes';
  else greeting.value = 'Buenas noches';
});
</script>

<template>
  <p class="text-[var(--color-primary)] font-semibold mt-2 text-lg">
    {{ greeting }}, {{ name }}
  </p>
</template>
