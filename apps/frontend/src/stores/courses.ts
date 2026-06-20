import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { coursesService } from '@/services/courses.service';
import type { Curso } from '@/types';

export const useCoursesStore = defineStore('courses', () => {
  const cursos = ref<Curso[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const enProgreso = computed(() => cursos.value.filter(c => c.progress > 0 && c.progress < 100));
  const disponibles = computed(() => cursos.value.filter(c => c.progress === 0));
  const completados = computed(() => cursos.value.filter(c => c.progress === 100));

  async function fetchCursos() {
    loading.value = true;
    error.value = null;
    try {
      cursos.value = await coursesService.getAll();
    } catch (e: any) {
      error.value = e.message || 'Error al cargar cursos';
    } finally {
      loading.value = false;
    }
  }

  function findCurso(id: string): Curso | undefined {
    return cursos.value.find(c => c.id === id);
  }

  return {
    cursos, loading, error,
    enProgreso, disponibles, completados,
    fetchCursos, findCurso,
  };
});
