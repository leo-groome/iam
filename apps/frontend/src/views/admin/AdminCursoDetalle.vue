<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';

const route = useRoute();
const router = useRouter();
const id = route.params.id as string;
const isNew = id === 'nuevo';
const curso = ref<any>(null);
const loading = ref(false);
const saving = ref(false);

// Form state
const formData = ref<any>({
  title: '',
  short_desc: '',
  long_desc: '',
  slug: '',
});

function onTitleInput() {
  if (isNew) {
    formData.value.slug = formData.value.title
      .toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9\s-]/g, '')
      .trim().replace(/\s+/g, '-');
  }
}

onMounted(async () => {
  if (!isNew) {
    loading.value = true;
    try {
      curso.value = await adminService.getCourse(id);
      // Populate form with loaded data
      formData.value = {
        title: curso.value?.title ?? '',
        short_desc: curso.value?.short_desc ?? '',
        long_desc: curso.value?.long_desc ?? '',
        slug: curso.value?.slug ?? '',
      };
    } catch (err) {
      console.error('Error loading course:', err);
    } finally {
      loading.value = false;
    }
  }
});

const saveCourse = async () => {
  saving.value = true;
  try {
    if (isNew) {
      await adminService.createCourse(formData.value);
    } else {
      await adminService.updateCourse(id, formData.value);
    }
    // Navigate back to courses list
    router.push('/admin/cursos');
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
  } catch (err) {
    console.error('Error publishing course:', err);
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
  } catch (err) {
    console.error('Error archiving course:', err);
  } finally {
    saving.value = false;
  }
};
</script>

<template>
  <div class="page-container">


  <router-link to="/admin/cursos" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Cursos</router-link>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Crear nuevo curso" : `Editar: ${formData.title || curso?.title}` }}</h1>
    <div class="flex gap-2">
      <button class="btn btn-secondary" type="button" @click="saveCourse" :disabled="saving">{{ saving ? "Guardando..." : "Guardar borrador" }}</button>
      <button class="btn btn-primary" type="button" @click="publishCourse" :disabled="isNew || saving">{{ saving ? "Publicando..." : "Publicar" }}</button>
    </div>
  </header>

  <div class="grid lg:grid-cols-3 gap-6">
    <div class="card p-6 lg:col-span-2 space-y-4">
      <div>
        <label class="label">Título del curso</label>
        <input class="input" minlength="5" maxlength="80" v-model="formData.title"
          @input="onTitleInput"
          placeholder="Ej. Comunicación empática" />
        <p class="help">5–80 caracteres.</p>
      </div>
      <div>
        <label class="label">Slug (URL)</label>
        <input class="input" minlength="2" maxlength="120" v-model="formData.slug"
          placeholder="ej. comunicacion-empatica" pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$" />
        <p class="help">Solo minúsculas, números y guiones. Se auto-genera del título.</p>
      </div>
      <div>
        <label class="label">Descripción corta</label>
        <input class="input" minlength="10" maxlength="160" v-model="formData.short_desc" placeholder="Una línea que resuma el curso" />
        <p class="help">Hasta 160 caracteres. Se muestra en la tarjeta.</p>
      </div>
      <div>
        <label class="label">Descripción larga</label>
        <textarea class="input min-h-32" maxlength="2000" v-model="formData.long_desc" placeholder="Markdown soportado"></textarea>
      </div>
      <div>
        <label class="label">Imagen de portada</label>
        <div class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-8 text-center text-sm text-[var(--color-text-muted)]">
          Arrastra o haz clic para subir (JPG/PNG/WebP · máx 2 MB · ratio 16:9)
        </div>
      </div>
    </div>

    <div class="space-y-6">
      <div class="card p-6">

        <h3 class="font-semibold mb-3">Configuración</h3>
        <div class="space-y-2 text-sm">
          <label class="flex items-center justify-between">
            <span>Estado de Publicación</span>
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
    </div>
  </div>

  <section v-if="!isNew && curso" class="mt-8">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-xl font-bold">Módulos</h2>
      <router-link :to="`/admin/cursos/${id}/modulos/nuevo`" class="btn btn-secondary">+ Agregar módulo</router-link>
    </div>
    <div class="space-y-3">
      <div v-for="(m, i) in curso.modules" :key="m.id" class="card p-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs text-[var(--color-text-muted)]">Módulo {{ i + 1 }}</p>
          <p class="font-semibold">{{ m.title }}</p>
          <p class="text-sm text-[var(--color-text-muted)] mt-1">{{ m.topics?.length ?? 0 }} temas · {{ m.duration }}</p>
        </div>
        <router-link :to="`/admin/cursos/${id}/modulos/${m.id}`" class="btn btn-secondary">Editar</router-link>
      </div>
    </div>
  </section>


  </div>
</template>
