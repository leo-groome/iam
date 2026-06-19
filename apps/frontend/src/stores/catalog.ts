import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiGet, type Course, type CourseList } from '@/lib/api'

export const useCatalogStore = defineStore('catalog', () => {
  const courses = ref<Course[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Hydrate the catalog from SSR props (typically the result of apiGet('/api/v1/courses')).
   */
  function hydrate(initial: Course[]) {
    courses.value = initial
    error.value = null
  }

  /**
   * Refetch courses from the API (CSR fallback, typically when data needs to refresh).
   */
  async function refetch() {
    loading.value = true
    error.value = null
    try {
      const result = await apiGet('/api/v1/courses')
      const data = result as CourseList
      courses.value = data.items || []
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch courses'
    } finally {
      loading.value = false
    }
  }

  /**
   * Get a course by slug.
   */
  function getBySlug(slug: string): Course | undefined {
    return courses.value.find(c => c.slug === slug)
  }

  return {
    courses,
    loading,
    error,
    hydrate,
    refetch,
    getBySlug,
  }
})
