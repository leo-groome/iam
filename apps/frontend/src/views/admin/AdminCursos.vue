<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { adminService } from '@/services/admin.service';
import SkeletonTable from '@/components/ui/SkeletonTable.vue';

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
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-100 transition-colors">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
                </div>
                <div>
                  <div class="font-bold text-gray-900 text-base mb-1">{{ c.title }}</div>
                  <div class="text-xs text-gray-500 truncate max-w-sm">{{ c.short_desc || 'Sin descripción' }}</div>
                </div>
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
