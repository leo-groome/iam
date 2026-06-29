<template>
  <PageProgressBar />
  <!-- Using a dynamic component depending on the route meta -->
  <component :is="layout">
    <router-view />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import PublicLayout from '@/layouts/PublicLayout.vue';
import StudentLayout from '@/layouts/StudentLayout.vue';
import AdminLayout from '@/layouts/AdminLayout.vue';
import PageProgressBar from '@/components/ui/PageProgressBar.vue';

const route = useRoute();

const layout = computed(() => {
  switch (route.meta.layout) {
    case 'AdminLayout':
      return AdminLayout;
    case 'StudentLayout':
      return StudentLayout;
    case 'PublicLayout':
    default:
      return PublicLayout;
  }
});
</script>
