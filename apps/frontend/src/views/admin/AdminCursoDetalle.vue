<script setup lang="ts">
import { useRoute } from 'vue-router';
import { onMounted, ref } from 'vue';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const slug = route.params.slug as string;
const isNew = slug === 'nuevo';
const curso = ref(null);
const loading = ref(false);

onMounted(async () => {
  if (!isNew) {
    loading.value = true;
    try {
      curso.value = await coursesService.getBySlug(slug);
    } catch (err) {
      console.error('Error loading course:', err);
    } finally {
      loading.value = false;
    }
  }
});
</script>

<template>
  <div class="page-container">


  <router-link to="/admin/cursos" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Cursos</router-link>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Crear nuevo curso" : `Editar: ${curso?.title}` }}</h1>
    <div class="flex gap-2">
      <button class="btn btn-secondary" type="button">Guardar borrador</button>
      <button class="btn btn-primary" type="button">Publicar</button>
    </div>
  </header>

  <div class="grid lg:grid-cols-3 gap-6">
    <div class="card p-6 lg:col-span-2 space-y-4">
      <div>
        <label class="label">Título del curso</label>
        <input class="input" minlength="5" maxlength="80" :value="curso?.title ?? ''" placeholder="Ej. Comunicación empática" />
        <p class="help">5–80 caracteres.</p>
      </div>
      <div>
        <label class="label">Descripción corta</label>
        <input class="input" maxlength="160" :value="curso?.short_desc ?? ''" placeholder="Una línea que resuma el curso" />
        <p class="help">Hasta 160 caracteres. Se muestra en la tarjeta.</p>
      </div>
      <div>
        <label class="label">Descripción larga</label>
        <textarea class="input min-h-32" maxlength="2000" placeholder="Markdown soportado">{{ curso?.long_desc ?? '' }}</textarea>
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
        <h3 class="font-semibold mb-3">Restricción por edad</h3>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Mínima</label>
            <input type="number" class="input" min="13" max="99" :value="curso?.age_min ?? 18" />
          </div>
          <div>
            <label class="label">Máxima</label>
            <input type="number" class="input" min="13" max="99" :value="curso?.age_max ?? 99" />
          </div>
        </div>
      </div>
      <div class="card p-6">
        <h3 class="font-semibold mb-3">Configuración</h3>
        <div class="space-y-2 text-sm">
          <label class="flex items-center justify-between">
            <span>Visible en catálogo</span>
            <input type="checkbox" checked />
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
      <router-link :to="`/admin/cursos/${curso.id}/modulos/nuevo`" class="btn btn-secondary">+ Agregar módulo</router-link>
    </div>
    <div class="space-y-3">
      <div v-for="(m, i) in curso.modulos" :key="m.id" class="card p-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs text-[var(--color-text-muted)]">Módulo {{ i + 1 }}</p>
          <p class="font-semibold">{{ m.title }}</p>
          <p class="text-sm text-[var(--color-text-muted)] mt-1">{{ m.temas.length }} temas · {{ m.duration }}</p>
        </div>
        <router-link :to="`/admin/cursos/${curso.id}/modulos/${m.id}`" class="btn btn-secondary">Editar</router-link>
      </div>
    </div>
  </section>


  </div>
</template>
