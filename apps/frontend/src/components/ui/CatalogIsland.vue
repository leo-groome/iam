<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { setActivePinia } from 'pinia'
import { newPinia } from '@/lib/pinia'
import { useCatalogStore } from '@/stores/catalog'
import { useProgressStore } from '@/stores/progress'
import CourseCard from '@/components/ui/CourseCard.vue'
import type { Course } from '@/lib/api'

interface Props {
  courses: Course[]
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  error: null,
})

// Local island state
const islandReady = ref(false)

// Create a fresh Pinia instance for this island (runs during both SSR and CSR)
const pinia = newPinia()
setActivePinia(pinia)

const catalogStore = useCatalogStore()
const progressStore = useProgressStore()

// Hydrate the catalog store with SSR data immediately
catalogStore.hydrate(props.courses)

onMounted(() => {
  islandReady.value = true
})

// Computed filters

const enProgreso = computed(() =>
  catalogStore.courses.filter(c => {
    const pct = progressStore.coursePercentage(c.slug)
    return pct > 0 && pct < 100
  })
)

const nuevos = computed(() =>
  catalogStore.courses.filter(c => {
    const pct = progressStore.coursePercentage(c.slug)
    return pct === 0
  })
)

const completados = computed(() =>
  catalogStore.courses.filter(c => {
    const pct = progressStore.coursePercentage(c.slug)
    return pct === 100
  })
)
</script>

<template>
  <div v-if="!islandReady" class="flex items-center justify-center min-h-screen">
    <div class="text-center">
      <div class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary-soft)] border-t-[var(--color-primary)]"></div>
    </div>
  </div>

  <div v-else-if="error" class="card p-6 text-center">
    <p class="text-red-600 font-semibold mb-2">Error al cargar el catálogo</p>
    <p class="text-[var(--color-text-muted)]">{{ error }}</p>
  </div>

  <div v-else class="space-y-10">
    <!-- En Progreso -->
    <section v-if="enProgreso.length > 0">
      <h2 class="text-lg font-semibold mb-3">Continuar donde lo dejé</h2>
      <div class="grid gap-4">
        <CourseCard
          v-for="course in enProgreso"
          :key="course.slug"
          :slug="course.slug"
          :title="course.title"
          :description="course.short_desc || course.description || ''"
          :cover="course.cover_key || course.cover_url || '/placeholder.jpg'"
          :progress="progressStore.coursePercentage(course.slug)"
        />
      </div>
    </section>

    <!-- Nuevos Cursos -->
    <section>
      <h2 class="text-lg font-semibold mb-3">Cursos disponibles</h2>
      <div v-if="nuevos.length > 0" class="grid gap-4">
        <CourseCard
          v-for="course in nuevos"
          :key="course.slug"
          :slug="course.slug"
          :title="course.title"
          :description="course.short_desc || course.description || ''"
          :cover="course.cover_key || course.cover_url || '/placeholder.jpg'"
          :progress="0"
        />
      </div>
      <div v-else class="card p-6 text-center text-[var(--color-text-muted)]">
        No hay cursos disponibles en este momento.
      </div>
    </section>

    <!-- Completados -->
    <section v-if="completados.length > 0">
      <h2 class="text-lg font-semibold mb-3">Ya completados</h2>
      <div class="grid gap-4">
        <CourseCard
          v-for="course in completados"
          :key="course.slug"
          :slug="course.slug"
          :title="course.title"
          :description="course.short_desc || course.description || ''"
          :cover="course.cover_key || course.cover_url || '/placeholder.jpg'"
          cta="Ver certificado"
          :href="`/curso/${course.slug}/certificado`"
          :progress="100"
        />
      </div>
    </section>
  </div>
</template>
