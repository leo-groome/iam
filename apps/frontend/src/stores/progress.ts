import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CourseProgress } from '@/lib/api'

/**
 * Track per-course progress (modules, topics, completion %).
 * CourseProgress structure: { course_pct: number, modules: ModuleProgressItem[] }
 */
export const useProgressStore = defineStore('progress', () => {
  const progressByCourse = ref<Record<string, CourseProgress>>({})

  /**
   * Hydrate progress for a specific course.
   */
  function hydrate(slug: string, data: CourseProgress) {
    progressByCourse.value[slug] = data
  }

  /**
   * Optimistically update course progress percentage.
   */
  function updateProgress(slug: string, percentage: number) {
    if (progressByCourse.value[slug]) {
      progressByCourse.value[slug].course_pct = Math.min(100, Math.max(0, percentage))
    }
  }

  /**
   * Get progress for a specific course.
   */
  const courseProgress = computed(() => {
    return (slug: string) => progressByCourse.value[slug] || null
  })

  /**
   * Get completion percentage for a course.
   */
  const coursePercentage = computed(() => {
    return (slug: string) => progressByCourse.value[slug]?.course_pct ?? 0
  })

  return {
    progressByCourse,
    hydrate,
    updateProgress,
    courseProgress,
    coursePercentage,
  }
})
