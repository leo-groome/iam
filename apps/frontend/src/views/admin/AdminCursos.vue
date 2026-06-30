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
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 17.25v1.007a3 3 0 0 1-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0 1 15 18.257V17.25m6-12V15a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 15V5.25m18 0A2.25 2.25 0 0 0 18.75 3H5.25A2.25 2.25 0 0 0 3 5.25m18 0V12a2.25 2.25 0 0 1-2.25 2.25H5.25A2.25 2.25 0 0 1 3 12V5.25" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.25 9.75 10.5 12V7.5l3.75 2.25Z" />
                  </svg>
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
