<script setup lang="ts">
import type { Course } from '@/lib/api'

interface Props {
  course: Course
  progress?: number
}

withDefaults(defineProps<Props>(), {
  progress: 0,
})

function navigateToCourse(slug: string) {
  window.location.href = `/curso/${slug}`
}

const buttonLabel = (progress: number) => {
  return progress > 0 && progress < 100 ? 'Continuar' : 'Comenzar'
}
</script>

<template>
  <a
    :href="`/curso/${course.slug}`"
    class="card overflow-hidden block hover:border-[var(--color-primary)] transition group flex flex-col md:flex-row"
  >
    <div
      class="relative shrink-0 overflow-hidden bg-white border-r border-[var(--color-border)] aspect-[16/9] md:aspect-auto md:w-[42%] md:max-w-xs grid place-items-center p-6"
    >
      <img
        src="/MISIONERAS_LOGO.svg"
        :alt="course.title"
        loading="lazy"
        class="max-w-[75%] max-h-[75%] w-auto h-auto object-contain group-hover:scale-105 transition duration-500"
      />
      <span
        v-if="progress === 100"
        class="absolute top-3 right-3 chip bg-emerald-500/95 text-white"
      >
        ✓ Completado
      </span>
    </div>
    <div class="p-5 md:p-6 flex flex-col flex-1 min-w-0">
      <h3 class="font-bold text-xl leading-tight mb-2">{{ course.title }}</h3>
      <p class="text-[var(--color-text-muted)] text-sm leading-relaxed mb-4 line-clamp-3">
        {{ course.description }}
      </p>
      <div class="flex flex-wrap gap-2 mb-4">
        <span class="chip">{{ course.duration_weeks || 4 }} semanas</span>
        <span class="chip">Examen corto</span>
      </div>
      <div v-if="progress > 0 && progress < 100" class="h-1.5 bg-[var(--color-primary-soft)] rounded-full overflow-hidden mb-3">
        <div class="h-full bg-[var(--color-primary)]" :style="{ width: `${progress}%` }"></div>
      </div>
      <span class="btn btn-primary mt-auto md:self-start group-hover:bg-[var(--color-primary-hover)]">
        {{ buttonLabel(progress) }}
      </span>
    </div>
  </a>
</template>
