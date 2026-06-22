<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';

const courses = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const data = await adminService.getCourses();
    courses.value = Array.isArray(data) ? data : (data as any).items ?? [];
  } catch (err) {
    console.error('Error loading courses:', err);
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page-container">


  <header class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-3xl font-bold">Cursos</h1>
      <p class="text-[var(--color-text-muted)]">Gestiona el contenido de la plataforma.</p>
    </div>
    <router-link to="/admin/cursos/nuevo" class="btn btn-primary">+ Crear curso</router-link>
  </header>

  <div class="card overflow-hidden">
    <table class="w-full text-sm">
      <thead class="bg-[var(--color-app-bg)] text-left text-[var(--color-text-muted)]">
        <tr>
          <th class="px-4 py-3 font-medium">Título</th>
          <th class="px-4 py-3 font-medium">Módulos</th>
          <th class="px-4 py-3 font-medium">Edad</th>
          <th class="px-4 py-3 font-medium">Estado</th>
          <th class="px-4 py-3 font-medium"></th>
        </tr>
      </thead>
      <tbody class="divide-y divide-[var(--color-border)]">
        <tr v-for="c in courses" :key="c.id" class="hover:bg-[var(--color-app-bg)]">
          <td class="px-4 py-3 font-medium">{{ c.title }}</td>
          <td class="px-4 py-3">{{ c.modules?.length ?? '-' }}</td>
          <td class="px-4 py-3 text-[var(--color-text-muted)]">{{ c.age_min }}–{{ c.age_max }}</td>
          <td class="px-4 py-3"><span class="chip">{{ c.status }}</span></td>
          <td class="px-4 py-3 text-right">
            <router-link :to="`/admin/cursos/${c.id}`" class="text-[var(--color-primary)] font-medium">Editar</router-link>
          </td>
        </tr>
      </tbody>
    </table>
  </div>


  </div>
</template>
