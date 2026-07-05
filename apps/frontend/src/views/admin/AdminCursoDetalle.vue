<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { computed, onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';
import { mediaService } from '@/services/media.service';

const route = useRoute();
const router = useRouter();
const id = route.params.id as string;
const isNew = id === 'nuevo';
const curso = ref<any>(null);
const loading = ref(false);
const saving = ref(false);

const isUploadingCover = ref(false);
const isUploadingMedia = ref(false);
const deleteConfirmOpen = ref(false);
const deleteConfirmText = ref('');
const deleteError = ref('');

// Form state
const formData = ref<any>({
  title: '',
  short_desc: '',
  long_desc: '',
  slug: '',
  cover_key: null,
});

function onTitleInput() {
  if (isNew) {
    formData.value.slug = formData.value.title
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9\s-]/g, '')
      .trim().replace(/\s+/g, '-');
  }
}

const loadCourse = async () => {
  if (!isNew) {
    loading.value = true;
    try {
      curso.value = await adminService.getCourse(id);
      formData.value = {
        title: curso.value?.title ?? '',
        short_desc: curso.value?.short_desc ?? '',
        long_desc: curso.value?.long_desc ?? '',
        slug: curso.value?.slug ?? '',
        cover_key: curso.value?.cover_key ?? null,
      };
    } catch (err) {
      console.error('Error loading course:', err);
    } finally {
      loading.value = false;
    }
  }
};

onMounted(async () => {
  if (isNew) {
    openCourseDrawer();
  } else {
    await loadCourse();
  }
});

const saveCourse = async () => {
  saving.value = true;
  try {
    if (isNew) {
      const newCourse = await adminService.createCourse(formData.value);
      if (newCourse && newCourse.id) {
        router.push(`/admin/cursos/${newCourse.id}`);
        return;
      }
    } else {
      await adminService.updateCourse(id, formData.value);
    }
    if (!isNew) {
      router.push('/admin/cursos');
    }
  } catch (err) {
    console.error('Error saving course:', err);
  } finally {
    saving.value = false;
  }
};

const publishCourse = async () => {
  if (isNew) return;
  saving.value = true;
  try {
    await adminService.publishCourse(id);
    router.push('/admin/cursos');
  } catch (err: any) {
    console.error('Error publishing course:', err);
    alert('Error al publicar: ' + (err.message || 'Error desconocido'));
  } finally {
    saving.value = false;
  }
};

const archiveCourse = async () => {
  if (isNew) return;
  if (!confirm('¿Estás seguro de que deseas archivar este curso?')) return;
  saving.value = true;
  try {
    await adminService.archiveCourse(id);
    router.push('/admin/cursos');
  } catch (err: any) {
    console.error('Error archiving course:', err);
    alert('Error al archivar: ' + (err.message || 'Error desconocido'));
  } finally {
    saving.value = false;
  }
};

const deleteCourseAction = async () => {
  if (isNew) return;
  deleteConfirmText.value = '';
  deleteError.value = '';
  deleteConfirmOpen.value = true;
};

const closeDeleteConfirm = () => {
  if (saving.value) return;
  deleteConfirmOpen.value = false;
  deleteConfirmText.value = '';
  deleteError.value = '';
};

const requiredDeleteTitle = computed(() => curso.value?.title || formData.value.title || '');
const canConfirmDelete = computed(() => deleteConfirmText.value === requiredDeleteTitle.value);

const confirmDeleteCourse = async () => {
  if (isNew || !canConfirmDelete.value) return;
  saving.value = true;
  deleteError.value = '';
  try {
    await adminService.deleteCourse(id, deleteConfirmText.value);
    router.push('/admin/cursos');
  } catch (err: any) {
    console.error('Error deleting course:', err);
    deleteError.value = err.message || 'No se pudo eliminar el curso.';
  } finally {
    saving.value = false;
  }
};

const deleteModuleAction = async (modId: string) => {
  if (!confirm('¿Eliminar este módulo y todas sus clases? Esta acción no se puede deshacer.')) return;
  try {
    await adminService.deleteModule(modId);
    await loadCourse();
  } catch (err: any) {
    console.error('Error deleting module:', err);
    alert('Error al eliminar módulo: ' + (err.message || 'Error desconocido'));
  }
};

const deleteTopicAction = async (topicId: string) => {
  if (!confirm('¿Eliminar esta clase? Esta acción no se puede deshacer.')) return;
  try {
    await adminService.deleteTopic(topicId);
    await loadCourse();
  } catch (err: any) {
    console.error('Error deleting topic:', err);
    alert('Error al eliminar clase: ' + (err.message || 'Error desconocido'));
  }
};

const handleCoverUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  isUploadingCover.value = true;
  try {
    const key = await mediaService.uploadFile(file, 'cover');
    formData.value.cover_key = key;
  } catch (err: any) {
    console.error('Error uploading cover:', err);
    alert('No se pudo subir la imagen de portada: ' + err.message);
  } finally {
    isUploadingCover.value = false;
  }
};

const handleTopicMediaUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  let scope: 'video' | 'pdf' | 'imagen' = 'imagen';
  if (drawerData.value.content_type === 'video') scope = 'video';
  else if (drawerData.value.content_type === 'pdf') scope = 'pdf';

  isUploadingMedia.value = true;
  try {
    const key = await mediaService.uploadFile(file, scope);
    drawerData.value.content_url = key;
  } catch (err: any) {
    console.error('Error uploading topic media:', err);
    alert('No se pudo subir el archivo: ' + err.message);
  } finally {
    isUploadingMedia.value = false;
  }
};

// --- CURRICULUM BUILDER LOGIC ---
const expandedModules = ref<string[]>([]);
const isExpanded = (modId: string) => expandedModules.value.includes(modId);
const toggleModule = (modId: string) => {
  if (isExpanded(modId)) {
    expandedModules.value = expandedModules.value.filter(id => id !== modId);
  } else {
    expandedModules.value.push(modId);
  }
};

// Drawer state
const drawerOpen = ref(false);
const drawerType = ref<'module' | 'topic' | 'course'>('module');
const drawerMode = ref<'new' | 'edit'>('new');
const activeModuleId = ref<string | null>(null);
const activeTopicId = ref<string | null>(null);
const drawerSaving = ref(false);

const drawerData = ref<any>({});

const closeDrawer = () => {
  drawerOpen.value = false;
  drawerData.value = {};
  activeModuleId.value = null;
  activeTopicId.value = null;
  // If we closed the course drawer while creating a new course, go back
  if (drawerType.value === 'course' && isNew) {
    router.push('/admin/cursos');
  }
};

const openCourseDrawer = () => {
  drawerType.value = 'course';
  drawerMode.value = isNew ? 'new' : 'edit';
  drawerOpen.value = true;
};



const openModuleDrawer = (modId: string | 'nuevo') => {
  drawerType.value = 'module';
  if (modId === 'nuevo') {
    drawerMode.value = 'new';
    drawerData.value = { title: '', description: '', max_attempts: 3 };
  } else {
    drawerMode.value = 'edit';
    activeModuleId.value = modId;
    const mod = curso.value?.modules?.find((m: any) => m.id === modId);
    drawerData.value = { 
      title: mod?.title ?? '', 
      description: mod?.description ?? '',
      max_attempts: mod?.max_attempts ?? 3 
    };
  }
  drawerOpen.value = true;
};

const openTopicDrawer = (modId: string, topicId: string | 'nuevo') => {
  drawerType.value = 'topic';
  activeModuleId.value = modId;
  if (topicId === 'nuevo') {
    drawerMode.value = 'new';
    drawerData.value = { 
      title: '', 
      content_type: 'video', 
      content_body: '', 
      duration_minutes: null, 
      has_exam: false, 
      exam_min_score: 70 
    };
  } else {
    drawerMode.value = 'edit';
    activeTopicId.value = topicId;
    const mod = curso.value?.modules?.find((m: any) => m.id === modId);
    const topic = mod?.topics?.find((t: any) => t.id === topicId);
    drawerData.value = { 
      title: topic?.title ?? '', 
      content_type: topic?.content_type ?? 'video', 
      content_body: topic?.content_body ?? '', 
      duration_minutes: topic?.duration_seconds ? Math.round(topic.duration_seconds / 60) : null,
      has_exam: topic?.has_exam ?? false,
      exam_min_score: topic?.exam_min_score ?? 70,
      content_url: topic?.media_key ?? ''
    };
  }
  drawerOpen.value = true;
};

const saveDrawer = async () => {
  drawerSaving.value = true;
  try {
    if (drawerType.value === 'course') {
      await saveCourse();
      closeDrawer();
      return;
    } else if (drawerType.value === 'module') {
      const payload = {
        title: drawerData.value.title,
        description: drawerData.value.description,
        max_attempts: drawerData.value.max_attempts,
      };
      if (drawerMode.value === 'new') {
        await adminService.createModule(id, payload);
      } else {
        await adminService.updateModule(activeModuleId.value!, payload);
      }
    } else if (drawerType.value === 'topic') {
      const dur = drawerData.value.duration_minutes ? Number(drawerData.value.duration_minutes) * 60 : null;
      const payload = {
        title: drawerData.value.title,
        content_type: drawerData.value.content_type,
        has_exam: drawerData.value.has_exam,
        content_body: drawerData.value.content_body || null,
        duration_seconds: dur,
        exam_min_score: Number(drawerData.value.exam_min_score) || 70,
        media_key: drawerData.value.content_url || null,
      };
      if (drawerMode.value === 'new') {
        await adminService.createTopic(activeModuleId.value!, payload);
        if (!isExpanded(activeModuleId.value!)) toggleModule(activeModuleId.value!);
      } else {
        await adminService.updateTopic(activeTopicId.value!, payload);
      }
    }
    closeDrawer();
    await loadCourse(); // Refresh curriculum tree
  } catch (err) {
    console.error('Error saving item:', err);
  } finally {
    drawerSaving.value = false;
  }
};
</script>

<template>
  <div class="page-container relative min-h-screen">

  <div class="mb-4 text-sm text-[var(--color-text-muted)] flex items-center gap-2">
    <router-link to="/admin/cursos" class="hover:text-[var(--color-primary)] transition-colors">Cursos</router-link>
    <span v-if="!isNew">/</span>
    <span v-if="!isNew" class="font-medium text-[var(--color-text)]">{{ formData.title || curso?.title }}</span>
  </div>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Crear nuevo curso" : `Configuración de Curso` }}</h1>
    <div class="flex gap-2">
      <button v-if="!isNew" class="btn border border-gray-300 text-gray-600 hover:bg-gray-50" type="button" @click="archiveCourse" :disabled="saving">Archivar</button>
      <button v-if="!isNew" class="btn border border-red-200 text-red-600 hover:bg-red-50" type="button" @click="deleteCourseAction" :disabled="saving">Eliminar</button>
      <button class="btn btn-primary" type="button" @click="publishCourse" :disabled="isNew || saving">{{ saving ? "Publicando..." : "Publicar" }}</button>
    </div>
  </header>

  <Transition name="fade">
    <div
      v-if="deleteConfirmOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-course-title"
      @click.self="closeDeleteConfirm"
    >
      <form class="card w-full max-w-lg p-6 shadow-2xl" @submit.prevent="confirmDeleteCourse">
        <div class="flex items-start gap-4">
          <div class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-red-100 text-red-700">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
          </div>
          <div class="min-w-0">
            <h2 id="delete-course-title" class="text-xl font-bold text-red-700">Eliminar curso permanentemente</h2>
            <p class="mt-2 text-sm text-[var(--color-text-muted)]">
              Esta acción eliminará el curso y su estructura. No se puede deshacer.
            </p>
          </div>
        </div>

        <div class="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Para confirmar, escribe exactamente:
          <strong class="mt-1 block break-words">{{ requiredDeleteTitle }}</strong>
        </div>

        <div class="mt-5">
          <label for="delete-course-confirmation" class="label">Nombre del curso</label>
          <input
            id="delete-course-confirmation"
            v-model="deleteConfirmText"
            class="input"
            autocomplete="off"
            :disabled="saving"
            :placeholder="requiredDeleteTitle"
          />
        </div>

        <p v-if="deleteError" class="mt-3 text-sm text-red-600">{{ deleteError }}</p>

        <div class="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button type="button" class="btn btn-secondary" :disabled="saving" @click="closeDeleteConfirm">
            Cancelar
          </button>
          <button
            type="submit"
            class="btn border border-red-600 bg-red-600 text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="saving || !canConfirmDelete"
          >
            {{ saving ? 'Eliminando...' : 'Eliminar definitivamente' }}
          </button>
        </div>
      </form>
    </div>
  </Transition>

  <div v-if="!isNew && curso" class="card p-6 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between mb-8 shadow-sm">
    <div class="flex items-center gap-4">
      <div class="w-16 h-16 bg-gray-200 rounded-lg overflow-hidden flex-shrink-0 border border-gray-300 flex items-center justify-center relative">
        <img v-if="formData.cover_url || formData.cover_key || curso?.cover_url || curso?.cover_key" 
             :src="formData.cover_url || formData.cover_key || curso?.cover_url || curso?.cover_key" 
             class="absolute inset-0 w-full h-full object-cover" 
             alt="Portada del curso" />
        <svg v-else class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
      </div>
      <div>
        <h2 class="text-xl font-bold">{{ formData.title }}</h2>
        <p class="text-sm text-[var(--color-text-muted)] mt-1 max-w-2xl">{{ formData.short_desc || 'Sin descripción' }}</p>
      </div>
    </div>
    <button type="button" @click="openCourseDrawer" class="btn btn-secondary whitespace-nowrap">
      <svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
      Ajustes del curso
    </button>
  </div>


  <!-- CURRICULUM BUILDER -->
  <section v-if="!isNew && curso" class="mt-8 pb-32">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="text-xl font-bold">Plan de Estudios (Currícula)</h2>
        <p class="text-sm text-[var(--color-text-muted)]">Organiza tu curso creando módulos y clases.</p>
      </div>
      <button type="button" @click="openModuleDrawer('nuevo')" class="btn btn-secondary">+ Agregar módulo</button>
    </div>
    
    <div v-if="curso.modules && curso.modules.length > 0" class="space-y-4">
      <div v-for="(m, i) in curso.modules" :key="m.id" class="border border-[var(--color-border)] rounded-xl overflow-hidden bg-[var(--color-surface)] shadow-sm">
        
        <!-- Accordion Header (Module) -->
        <div class="p-4 flex items-center justify-between cursor-pointer hover:bg-[var(--color-app-bg)] transition-colors select-none" @click="toggleModule(m.id)">
           <div class="flex items-center gap-3">
              <svg :class="['w-5 h-5 text-[var(--color-text-muted)] transition-transform', isExpanded(m.id) ? 'rotate-90' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
              <div>
                <p class="font-semibold">Módulo {{ i + 1 }}: {{ m.title }}</p>
                <p class="text-xs text-[var(--color-text-muted)] mt-0.5">{{ m.topics?.length ?? 0 }} clases <!-- duration --></p>
              </div>
           </div>
           <div class="flex gap-2">
             <button type="button" @click.stop="openModuleDrawer(m.id)" class="text-xs font-medium border border-[var(--color-primary)] text-black px-2 py-1 rounded hover:bg-[var(--color-primary)] hover:text-white transition-colors">Editar</button>
             <router-link :to="`/admin/cursos/${id}/modulos/${m.id}`" class="text-xs font-medium border border-[var(--color-primary)] text-black px-2 py-1 rounded hover:bg-[var(--color-primary)] hover:text-white transition-colors" @click.stop>Examen</router-link>
             <button type="button" @click.stop="deleteModuleAction(m.id)" class="text-xs font-medium border border-red-500 text-black px-2 py-1 rounded hover:bg-red-500 hover:text-white transition-colors">Eliminar</button>
           </div>
        </div>

        <!-- Accordion Body (Topics) -->
        <div v-show="isExpanded(m.id)" class="border-t border-[var(--color-border)] bg-[var(--color-app-bg)] p-4">
           <div class="space-y-2 mb-3">
             <div v-for="(t, j) in m.topics" :key="t.id" class="flex items-center justify-between p-3 bg-[var(--color-surface)] rounded-lg border border-[var(--color-border)] hover:border-[var(--color-border-hover)] transition-colors">
                <div class="flex items-center gap-3">
                   <span class="text-[10px] uppercase bg-blue-100 text-blue-700 font-bold px-2 py-1 rounded w-16 text-center">{{ t.content_type }}</span>
                   <span class="text-sm font-medium">{{ j + 1 }}. {{ t.title }}</span>
                </div>
                <div class="flex items-center gap-2">
                   <span v-if="t.has_exam" class="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-medium">Examen</span>
                   <button type="button" @click.stop="openTopicDrawer(m.id, t.id)" class="text-xs font-medium border border-[var(--color-primary)] text-black px-2 py-1 rounded hover:bg-[var(--color-primary)] hover:text-white transition-colors">Editar</button>
                   <router-link v-if="t.has_exam" :to="`/admin/cursos/${id}/modulos/${m.id}/temas/${t.id}/preguntas`" class="text-xs font-medium border border-[var(--color-primary)] text-black px-2 py-1 rounded hover:bg-[var(--color-primary)] hover:text-white transition-colors" @click.stop>Preguntas</router-link>
                   <button type="button" @click.stop="deleteTopicAction(t.id)" class="text-xs font-medium border border-red-500 text-black px-2 py-1 rounded hover:bg-red-500 hover:text-white transition-colors">Eliminar</button>
                </div>
             </div>
           </div>
           
           <button type="button" @click="openTopicDrawer(m.id, 'nuevo')" class="w-full text-left p-3 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:bg-[var(--color-surface)] hover:border-[var(--color-primary)] rounded-lg border border-dashed border-[var(--color-border)] transition-colors flex items-center justify-center gap-2">
             <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
             Agregar nueva clase
           </button>
        </div>
      </div>
    </div>
    <div v-else class="text-center p-8 border-2 border-dashed border-[var(--color-border)] rounded-xl mt-4 text-[var(--color-text-muted)] bg-[var(--color-surface)]">
      <p>Aún no hay contenido en este curso.</p>
      <button type="button" @click="openModuleDrawer('nuevo')" class="btn btn-secondary mt-3">+ Agregar tu primer módulo</button>
    </div>
  </section>

  <!-- SLIDE-OVER DRAWER OVERLAY -->
  <Transition name="fade">
    <div v-if="drawerOpen" class="fixed inset-0 bg-black/40 z-40 backdrop-blur-sm" @click="closeDrawer"></div>
  </Transition>

  <!-- SLIDE-OVER DRAWER PANEL -->
  <Transition name="slide-right">
    <div v-if="drawerOpen" class="fixed inset-y-0 right-0 w-full max-w-md bg-[var(--color-surface)] shadow-2xl z-50 flex flex-col border-l border-[var(--color-border)]">
      <!-- Drawer Header -->
      <div class="px-6 py-4 border-b border-[var(--color-border)] flex items-center justify-between bg-[var(--color-app-bg)]">
        <h3 class="text-lg font-bold">
          <span v-if="drawerType === 'course'">{{ isNew ? 'Crear Nuevo Curso' : 'Ajustes del Curso' }}</span>
          <span v-else>
            {{ drawerMode === 'new' ? 'Crear' : 'Editar' }} 
            {{ drawerType === 'module' ? 'Módulo' : 'Clase' }}
          </span>
        </h3>
        <button type="button" @click="closeDrawer" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <!-- Drawer Body -->
      <div class="flex-1 overflow-y-auto p-6 space-y-5">
        
        <!-- COURSE FORM -->
        <template v-if="drawerType === 'course'">
          <div>
            <label class="label">Título del curso</label>
            <input class="input" minlength="5" maxlength="80" v-model="formData.title" @input="onTitleInput" placeholder="Ej. Comunicación empática" />
            <p class="help">5–80 caracteres.</p>
          </div>
          <div>
            <label class="label">Slug (URL)</label>
            <input class="input" minlength="2" maxlength="120" v-model="formData.slug" placeholder="ej. comunicacion-empatica" pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$" />
            <p class="help">Solo minúsculas, números y guiones. Se auto-genera.</p>
          </div>
          <div>
            <label class="label">Descripción corta</label>
            <textarea class="input min-h-24" maxlength="160" v-model="formData.short_desc" placeholder="Una línea que resuma el curso"></textarea>
            <p class="help">Hasta 160 caracteres. Se muestra en la tarjeta.</p>
          </div>
          <div>
            <label class="label">Descripción larga</label>
            <textarea class="input min-h-32" maxlength="2000" v-model="formData.long_desc" placeholder="Markdown soportado"></textarea>
          </div>
          <div>
            <label class="label">Imagen de portada</label>
            <div v-if="formData.cover_key" class="relative group rounded-xl overflow-hidden mb-2 border border-[var(--color-border)] aspect-video bg-[var(--color-app-bg)] flex items-center justify-center">
              <span class="text-xs text-[var(--color-text-muted)] p-4 break-all text-center">Archivo subido: {{ formData.cover_key }}</span>
              <button type="button" @click="formData.cover_key = null" class="absolute top-2 right-2 p-1.5 rounded-full bg-red-600 text-white hover:bg-red-700 shadow-md z-20">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
              </button>
            </div>
            <div class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-4 text-center hover:bg-[var(--color-app-bg)] transition-colors relative cursor-pointer group">
              <input type="file" accept="image/jpeg, image/png, image/webp" @change="handleCoverUpload" :disabled="isUploadingCover" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
              <div v-if="isUploadingCover" class="flex flex-col items-center py-2">
                <svg class="animate-spin h-6 w-6 text-[var(--color-primary)] mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                <p class="text-sm text-[var(--color-text-muted)]">Subiendo imagen...</p>
              </div>
              <div v-else>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mx-auto text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)] transition-colors mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p class="text-sm text-[var(--color-text-muted)]">Arrastra o haz clic para subir</p>
              </div>
            </div>
          </div>
          <div class="pt-4 border-t border-[var(--color-border)]">
            <h4 class="font-semibold mb-3">Configuración de Publicación</h4>
            <div class="space-y-3 text-sm">
              <label class="flex items-center justify-between">
                <span>Estado</span>
                <select class="input py-1 text-sm w-32 bg-[var(--color-surface)]">
                  <option value="borrador">Borrador</option>
                  <option value="publicado" selected>Publicado</option>
                </select>
              </label>
              <label class="flex items-center justify-between">
                <span>Genera certificado</span>
                <input type="checkbox" checked />
              </label>
            </div>
          </div>
        </template>

        <!-- MODULE FORM -->
        <template v-if="drawerType === 'module'">
          <div>
            <label class="label">Título del módulo</label>
            <input class="input" minlength="3" maxlength="60" v-model="drawerData.title" placeholder="Ej: Introducción" />
          </div>
          <div>
            <label class="label">Descripción</label>
            <textarea class="input min-h-24" maxlength="2000" v-model="drawerData.description" placeholder="Objetivos del módulo..."></textarea>
          </div>
          <div class="pt-4 border-t border-[var(--color-border)]">
            <h4 class="font-semibold mb-2">Examen Diagnóstico</h4>
            <label class="label">Intentos Máximos</label>
            <input type="number" class="input max-w-24" min="1" max="10" v-model.number="drawerData.max_attempts" />
            <p class="text-xs text-[var(--color-text-muted)] mt-1">Límite antes de mostrar respuestas y avanzar.</p>
          </div>
        </template>

        <!-- TOPIC (CLASS) FORM -->
        <template v-if="drawerType === 'topic'">
          <div>
            <label class="label">Título de la clase</label>
            <input class="input" minlength="3" maxlength="60" v-model="drawerData.title" placeholder="Ej: ¿Qué es la comunicación?" />
          </div>
          <div>
            <label class="label">Tipo de contenido</label>
            <select class="input" v-model="drawerData.content_type">
              <option value="video">Video</option>
              <option value="pdf">PDF / Documento</option>
              <option value="imagen">Imagen / Infografía</option>
              <option value="texto">Artículo (Texto)</option>
            </select>
          </div>
          
          <div v-if="drawerData.content_type === 'texto'">
            <label class="label">Contenido del artículo</label>
            <textarea class="input min-h-32 text-sm font-mono" maxlength="20000" v-model="drawerData.content_body" placeholder="Soporta Markdown..."></textarea>
          </div>

          <div v-if="drawerData.content_type === 'video'">
            <label class="label">Duración aproximada (minutos)</label>
            <input type="number" class="input" v-model.number="drawerData.duration_minutes" min="1" placeholder="Ej: 15" />
          </div>

          <div v-if="drawerData.content_type !== 'texto'">
            <label class="label">Archivo Multimedia</label>
            <div v-if="drawerData.content_url" class="border border-[var(--color-border)] rounded-xl p-3 flex items-center justify-between bg-[var(--color-bg-hover)]">
              <div class="flex items-center gap-3 overflow-hidden">
                <svg class="w-8 h-8 text-[var(--color-primary)] flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <span class="text-sm font-medium truncate">{{ drawerData.content_url.split('/').pop() || 'Archivo actual' }}</span>
              </div>
              <button type="button" @click="drawerData.content_url = ''" class="text-xs text-red-600 hover:bg-red-50 px-2 py-1 rounded font-medium border border-red-200">Reemplazar</button>
            </div>
            <div v-else-if="isUploadingMedia" class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-6 text-center bg-[var(--color-app-bg)] flex flex-col items-center">
              <svg class="animate-spin h-6 w-6 text-[var(--color-primary)] mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              <p class="text-sm text-[var(--color-text-muted)]">Subiendo archivo a R2...</p>
            </div>
            <div v-else class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-4 text-center hover:bg-[var(--color-app-bg)] transition-colors relative cursor-pointer group">
              <input type="file" @change="handleTopicMediaUpload" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 mx-auto text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)] transition-colors mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
              <p class="text-sm font-medium text-[var(--color-text-muted)]">Arrastra o haz clic para subir archivo</p>
              <p class="text-xs text-[var(--color-text-muted)] mt-1">Max 500MB</p>
            </div>
          </div>

          <div class="pt-4 border-t border-[var(--color-border)]">
            <label class="flex items-center justify-between mb-2 cursor-pointer">
              <span class="font-semibold text-sm">Requiere Cuestionario / Examen</span>
              <input type="checkbox" v-model="drawerData.has_exam" />
            </label>
            <div v-if="drawerData.has_exam" class="mt-2">
              <label class="label">Puntaje mínimo para aprobar (%)</label>
              <input type="number" class="input max-w-24" min="50" max="100" v-model.number="drawerData.exam_min_score" />
            </div>
          </div>
        </template>

      </div>

      <!-- Drawer Footer -->
      <div class="p-4 border-t border-[var(--color-border)] bg-[var(--color-app-bg)] flex justify-end gap-3">
        <button type="button" @click="closeDrawer" class="btn btn-secondary">Cancelar</button>
        <button type="button" @click="saveDrawer" :disabled="drawerSaving" class="btn btn-primary min-w-24">
          {{ drawerSaving ? 'Guardando...' : 'Guardar' }}
        </button>
      </div>
    </div>
  </Transition>


  </div>
</template>

<style scoped>
/* Animations for the Drawer */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
