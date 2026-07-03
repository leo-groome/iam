<script setup lang="ts">
import { onMounted, onActivated, ref } from 'vue';
import { adminService } from '@/services/admin.service';
import SkeletonTable from '@/components/ui/SkeletonTable.vue';

const courses = ref([]);
const loading = ref(true);
let initialized = false;

const loadCourses = async () => {
  try {
    const data = await adminService.getCourses();
    courses.value = Array.isArray(data) ? data : (data as any).items ?? [];
  } catch (err) {
    console.error('Error loading courses:', err);
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await loadCourses();
  initialized = true;
});

onActivated(() => {
  if (initialized) {
    loadCourses(); // Recargar en segundo plano (lazy fetch) cuando la vista vuelve a activarse
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

  <transition name="fade" mode="out-in">
    <SkeletonTable v-if="loading" :rows="5" :columns="5" :hasAvatar="false" />
    <div v-else class="card overflow-hidden shadow-sm border border-[var(--color-border)] rounded-xl bg-white">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 border-b border-[var(--color-border)] text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
          <tr>
            <th class="px-6 py-4">Curso</th>
            <th class="px-6 py-4">Estado</th>
            <th class="px-6 py-4 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-[var(--color-border)]">
          <tr v-for="c in courses" :key="c.id" class="hover:bg-slate-50 transition-colors group cursor-pointer" @click="$router.push(`/admin/cursos/${c.id}`)">
            <td class="px-6 py-4">
              <div>
                <div class="font-bold text-gray-900 text-base mb-1">{{ c.title }}</div>
                <div class="text-xs text-gray-500 truncate max-w-sm">{{ c.short_desc || 'Sin descripción' }}</div>
              </div>
            </td>
            <td class="px-6 py-4">
              <span :class="[
                'px-3 py-1 rounded-full text-xs font-semibold border',
                c.status === 'publicado' ? 'bg-green-50 text-green-700 border-green-200' : 
                (c.status === 'archivado' ? 'bg-gray-50 text-gray-600 border-gray-200' : 'bg-amber-50 text-amber-700 border-amber-200')
              ]">
                {{ c.status.charAt(0).toUpperCase() + c.status.slice(1) }}
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <router-link :to="`/admin/cursos/${c.id}`" class="inline-flex items-center justify-center px-4 py-2 border border-blue-600 rounded text-sm font-medium text-black bg-white hover:bg-blue-600 hover:text-white transition-colors" @click.stop>
                Editar
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </transition>


  </div>
</template>
