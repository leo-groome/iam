<script setup lang="ts">
import { computed } from 'vue';
import { sanitizeHtml } from '@/lib/sanitize';

interface Props {
  slug: string;
  title: string;
  description: string;
  duration?: string;
  progress?: number;
  cover?: string;
  cta?: string;
  href?: string;
}

const props = withDefaults(defineProps<Props>(), {
  progress: 0,
  duration: ''
});

const url = computed(() => props.href ?? `/curso/${props.slug}`);
const buttonLabel = computed(() => props.cta ?? (props.progress > 0 ? "Continuar" : "Comenzar"));
</script>

<template>
  <router-link :to="url" class="card overflow-hidden block hover:border-[var(--color-primary)] transition group flex flex-col md:flex-row rounded-3xl">
    <div :class="['relative shrink-0 overflow-hidden bg-white border-r border-[var(--color-border)] aspect-[16/9] md:aspect-auto md:w-[42%] md:max-w-xs grid place-items-center', cover && cover !== '/placeholder.jpg' ? 'p-0' : 'p-6']">
      <img
        :src="cover && cover !== '/placeholder.jpg' ? cover : '/MISIONERAS_LOGO.svg'"
        :alt="title"
        loading="lazy"
        :class="[cover && cover !== '/placeholder.jpg' ? 'w-full h-full object-cover' : 'w-24 h-24 object-contain opacity-80', 'group-hover:scale-105 transition duration-500']"
      />
      <span v-if="progress === 100" class="absolute top-3 right-3 chip bg-emerald-500/95 text-white">✓ Completado</span>
    </div>
    <div class="p-5 md:p-6 flex flex-col flex-1 min-w-0">
      <h3 class="font-bold text-xl leading-tight mb-2">{{ title }}</h3>
      <div class="rich-text text-[var(--color-text-muted)] text-sm leading-relaxed mb-4 line-clamp-3" v-html="sanitizeHtml(description)"></div>
      <div class="flex flex-wrap gap-2 mb-4">
        <span v-if="duration" class="chip">{{ duration }}</span>
        <span class="chip">Examen corto</span>
      </div>
      <div v-if="progress < 100" class="mb-3">
        <div class="flex justify-between text-xs mb-1.5">
          <span class="font-medium text-[var(--color-text-muted)]">Progreso</span>
          <span class="font-bold text-[var(--color-primary)]">{{ Number(progress) || 0 }}%</span>
        </div>
        <div class="h-1.5 bg-[var(--color-primary-soft)] rounded-full overflow-hidden">
          <div class="h-full bg-[var(--color-primary)] transition-all duration-500" :style="{ width: `${Number(progress) || 0}%` }"></div>
        </div>
      </div>
      <span class="btn btn-primary mt-auto md:self-start group-hover:bg-[var(--color-primary-hover)]">{{ buttonLabel }}</span>
    </div>
  </router-link>
</template>
