<template>
  <PageProgressBar />
  <component :is="layout">
    <router-view v-slot="{ Component, route }">
      <keep-alive>
        <component 
          v-if="route.meta.keepAlive" 
          :is="Component" 
          :key="route.name" 
        />
      </keep-alive>
      <component 
        v-if="!route.meta.keepAlive" 
        :is="Component" 
        :key="route.fullPath" 
      />
    </router-view>
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
