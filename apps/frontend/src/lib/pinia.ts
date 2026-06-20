import { createPinia } from 'pinia'

/**
 * Create a fresh Pinia instance for a Vue island.
 *
 * Astro islands don't share state between them, so each client:load component
 * needs its own Pinia instance. Call this in a Vue component's onMounted hook.
 *
 * Usage:
 *   import { newPinia } from '@/lib/pinia'
 *   import { setActivePinia } from 'pinia'
 *
 *   onMounted(() => {
 *     const pinia = newPinia()
 *     setActivePinia(pinia)
 *     const store = useCatalogStore()
 *     // ...
 *   })
 */
export function newPinia() {
  return createPinia()
}
