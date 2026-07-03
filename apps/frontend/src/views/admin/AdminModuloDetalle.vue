<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';

const route = useRoute();
const router = useRouter();
const courseId = route.params.id as string;
const modId = route.params.modId as string;

const isNew = modId === 'nuevo';
const curso = ref(null);
const mod = ref(null);
const loading = ref(false);
const saving = ref(false);

// Form state
const formData = ref<any>({
  title: '',
  description: '',
  max_attempts: 3,
});

// Examen diagnóstico
const moduleQuestions = ref<any[]>([]);
const loadingQuestions = ref(false);

onMounted(async () => {
  loading.value = true;
  try {
    curso.value = await adminService.getCourse(courseId);
    if (!isNew) {
      mod.value = curso.value?.modules?.find((m: any) => m.id === modId) ?? null;
      if (mod.value) {
        formData.value = {
          title: mod.value.title ?? '',
          description: mod.value.description ?? '',
          max_attempts: mod.value.max_attempts ?? 3,
        };
      }
      // Load module-level diagnostic questions
      loadingQuestions.value = true;
      try {
        moduleQuestions.value = await adminService.listModuleQuestions(modId);
      } catch (err) {
        console.error('Error loading module questions:', err);
      } finally {
        loadingQuestions.value = false;
      }
    }
  } catch (err) {
    console.error('Error loading course:', err);
  } finally {
    loading.value = false;
  }
});

const handleSave = async () => {
  saving.value = true;
  try {
    if (isNew) {
      await adminService.createModule(courseId, {
        title: formData.value.title,
        description: formData.value.description,
        max_attempts: formData.value.max_attempts,
      });
    } else {
      await adminService.updateModule(modId, {
        title: formData.value.title,
        description: formData.value.description,
        max_attempts: formData.value.max_attempts,
      });
    }
  } catch (err) {
    console.error('Error saving module:', err);
  } finally {
    saving.value = false;
  }
};

const handleDeleteModule = async () => {
  if (!confirm('¿Eliminar este módulo y todas sus clases permanentemente? Esta acción no se puede deshacer.')) return;
  try {
    await adminService.deleteModule(modId);
    router.push(`/admin/cursos/${courseId}`);
  } catch (err: any) {
    console.error('Error deleting module:', err);
    alert('Error al eliminar módulo: ' + (err.message || 'Error desconocido'));
  }
};

const handleDeleteModuleQuestion = async (qId: string) => {
  try {
    await adminService.archiveQuestion(qId);
    moduleQuestions.value = moduleQuestions.value.filter(q => q.id !== qId);
  } catch (err: any) {
    console.error('Error deleting module question:', err);
    alert('Error al eliminar pregunta: ' + (err.message || 'Error desconocido'));
  }
};

const getContentTypeBadgeColor = (contentType: string): string => {
  switch (contentType) {
    case 'video':
      return 'bg-blue-600';
    case 'pdf':
      return 'bg-red-600';
    case 'texto':
      return 'bg-gray-600';
    case 'imagen':
      return 'bg-green-600';
    default:
      return 'bg-gray-600';
  }
};
</script>

<template>
  <div class="page-container">


  <div class="mb-4 text-sm text-[var(--color-text-muted)] flex items-center gap-2">
    <router-link to="/admin/cursos" class="hover:text-[var(--color-primary)] transition-colors">Cursos</router-link>
    <span>/</span>
    <router-link :to="`/admin/cursos/${courseId}`" class="hover:text-[var(--color-primary)] transition-colors">{{ curso?.title || 'Curso' }}</router-link>
    <span v-if="!isNew">/</span>
    <span v-if="!isNew" class="font-medium text-[var(--color-text)]">{{ formData.title || mod?.title }}</span>
  </div>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Nuevo módulo" : `Editar: ${mod?.title}` }}</h1>
    <div class="flex gap-2">
      <button v-if="!isNew" @click="handleDeleteModule" class="btn border border-red-200 text-red-600 hover:bg-red-50">Eliminar módulo</button>
      <button @click="handleSave" :disabled="saving" class="btn btn-primary">{{ saving ? "Guardando..." : "Guardar" }}</button>
    </div>
  </header>

  <div class="card p-6 mb-6 space-y-4">
    <div>
      <label class="label">Título</label>
      <input class="input" minlength="3" maxlength="60" v-model="formData.title" />
    </div>
    <div>
      <label class="label">Descripción del módulo</label>
      <textarea class="input min-h-24" maxlength="2000" v-model="formData.description" placeholder="Describe el contenido y objetivos del módulo"></textarea>
      <p class="help">Hasta 2000 caracteres.</p>
    </div>
    <div class="pt-2 border-t border-[var(--color-border)] mt-4">
      <h3 class="font-semibold mb-3">Configuración del Examen Diagnóstico</h3>
      <div>
        <label class="label">Intentos Máximos</label>
        <div class="flex items-center gap-4">
          <input type="number" class="input max-w-24" min="1" max="10" v-model.number="formData.max_attempts" />
          <p class="text-sm text-[var(--color-text-muted)]">
            Si el estudiante agota los intentos, se mostrarán las respuestas correctas y avanzará al siguiente módulo sin importar su calificación final.
          </p>
        </div>
      </div>
    </div>
  </div>

  <section v-if="!isNew && mod" class="mb-8">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-xl font-bold">Clases</h2>
      <router-link :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/nuevo`" class="btn btn-secondary">+ Nueva Clase</router-link>
    </div>
    <div v-if="mod.topics && mod.topics.length > 0" class="space-y-3">
      <router-link
        v-for="(t, i) in mod.topics"
        :key="t.id"
        :to="`/admin/cursos/${courseId}/modulos/${modId}/temas/${t.id}`"
        class="card p-4 flex items-center justify-between gap-3 hover:bg-[var(--color-bg-hover)] cursor-pointer transition-colors"
      >
        <div class="flex items-center gap-3 flex-1">
          <span :class="[getContentTypeBadgeColor(t.content_type), 'text-white text-xs font-semibold px-2 py-1 rounded']">
            {{ t.content_type }}
          </span>
          <div>
            <p class="text-xs text-[var(--color-text-muted)]">Clase {{ i + 1 }}</p>
            <p class="font-semibold">{{ t.title }}</p>
            <p class="text-sm text-[var(--color-text-muted)]">
              {{ t.duration_seconds ? Math.round(t.duration_seconds / 60) : '–' }} min
              <span v-if="t.has_exam" class="ml-2">· Con examen</span>
            </p>
          </div>
        </div>
        <svg class="w-5 h-5 text-[var(--color-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </router-link>
    </div>
    <div v-else class="card p-4 text-center text-sm text-[var(--color-text-muted)]">
      <p>No hay clases aún. Crea una para empezar.</p>
    </div>
  </section>

  <!-- Examen Diagnóstico del Módulo -->
  <section v-if="!isNew && mod">
    <div class="flex items-center justify-between mb-1">
      <div>
        <h2 class="text-xl font-bold">Examen Diagnóstico del Módulo</h2>
        <p class="text-sm text-[var(--color-text-muted)] mt-0.5">Preguntas que se aplican al completar todas las clases del módulo. Opcional.</p>
      </div>
      <router-link
        :to="`/admin/cursos/${courseId}/modulos/${modId}/examen-diagnostico/nueva`"
        class="btn btn-secondary"
      >
        + Nueva Pregunta Diagnóstica
      </router-link>
    </div>

    <div v-if="loadingQuestions" class="card p-4 text-center text-sm text-[var(--color-text-muted)] mt-3">
      <p>Cargando preguntas...</p>
    </div>
    <div v-else-if="moduleQuestions.length > 0" class="space-y-3 mt-3">
      <div v-for="(p, i) in moduleQuestions" :key="p.id" class="card p-5">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1">
            <p class="text-xs text-[var(--color-text-muted)] mb-1">Pregunta {{ i + 1 }}</p>
            <p class="font-semibold">{{ p.enunciado }}</p>
            <p class="text-sm text-[var(--color-text-muted)] mt-1">{{ p.options?.length ?? 0 }} opciones</p>
          </div>
          <div class="flex gap-2">
            <router-link
              :to="`/admin/cursos/${courseId}/modulos/${modId}/examen-diagnostico/${p.id}`"
              class="btn btn-secondary"
            >
              Editar
            </router-link>
            <button
              @click="handleDeleteModuleQuestion(p.id)"
              class="btn btn-secondary text-[var(--color-error)]"
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="card p-4 text-center text-sm text-[var(--color-text-muted)] mt-3">
      <p>No hay preguntas diagnósticas. Agrega una para configurar el examen del módulo.</p>
    </div>
  </section>


  </div>
</template>
