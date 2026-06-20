import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/lib/api'

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Hydrate the user from SSR props (typically Astro.locals.user).
   */
  function hydrate(initial: User | null) {
    user.value = initial
  }

  /**
   * Set a user directly (e.g., after login or from API fetch).
   */
  function setUser(u: User | null) {
    user.value = u
    error.value = null
  }

  /**
   * Clear the user (logout).
   */
  function clear() {
    user.value = null
    error.value = null
  }

  /**
   * Set error state (e.g., failed fetch or auth error).
   */
  function setError(msg: string | null) {
    error.value = msg
  }

  /**
   * Computed: is user authenticated?
   */
  const isAuthenticated = computed(() => user.value !== null && user.value !== undefined)

  /**
   * Computed: is user an admin?
   */
  const isAdmin = computed(() => user.value?.role === 'admin')

  /**
   * Computed: is user an instructor?
   */
  const isInstructor = computed(() => user.value?.role === 'instructor')

  /**
   * Computed: helper to check user roles.
   * Note: birth_date is stored separately in the session, not in User.
   * Age validation happens server-side via /auth/sync.
   */
  const isStudent = computed(() => user.value?.role === 'estudiante')

  return {
    user,
    loading,
    error,
    hydrate,
    setUser,
    clear,
    setError,
    isAuthenticated,
    isAdmin,
    isInstructor,
    isStudent,
  }
})
