<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { adminService } from '@/services/admin.service'
import SkeletonTable from '@/components/ui/SkeletonTable.vue'
import UserAvatar from '@/components/ui/UserAvatar.vue'

const students = ref<any[]>([])
const loading = ref(true)
const search = ref('')
const statusFilter = ref('')

async function fetchStudents() {
  loading.value = true
  const res = await adminService.getStudents({
    q: search.value || undefined,
    status: statusFilter.value || undefined,
  })
  students.value = res?.items ?? []
  loading.value = false
}

onMounted(fetchStudents)
watch([search, statusFilter], fetchStudents)
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-6 animate-fade-in">
    <header class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-[var(--color-text)]">Directorio de Estudiantes</h1>
        <p class="text-[var(--color-text-muted)] mt-1">Gestiona el progreso y los accesos de los alumnos</p>
      </div>
    </header>

    <!-- Filtros -->
    <div class="card p-4 flex flex-col md:flex-row gap-4 items-center">
      <div class="relative flex-1 w-full">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        <input v-model="search" type="text" placeholder="Buscar por nombre o correo electrónico..." class="input pl-10 w-full" />
      </div>
      <div class="w-full md:w-64 shrink-0">
        <select v-model="statusFilter" class="input w-full">
          <option value="">Todos los estados</option>
          <option value="active">Activo</option>
          <option value="inactive">Inactivo</option>
          <option value="stuck">Atascado (Requiere atención)</option>
        </select>
      </div>
    </div>

    <!-- Tabla -->
    <transition name="fade" mode="out-in">
      <SkeletonTable v-if="loading" :rows="5" :columns="4" :hasAvatar="true" />
      <div v-else class="card overflow-hidden">
        
        <div v-if="students.length === 0" class="text-[var(--color-text-muted)] text-center py-16 flex flex-col items-center">
          <svg class="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
          <h3 class="text-lg font-semibold text-[var(--color-text)]">No se encontraron estudiantes</h3>
          <p class="mt-1">Intenta ajustando los filtros o el término de búsqueda.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-[var(--color-bg-hover)] border-b border-[var(--color-border)] text-sm">
                <th class="px-6 py-4 font-semibold">Nombre Completo</th>
                <th class="px-6 py-4 font-semibold">Correo Electrónico</th>
                <th class="px-6 py-4 font-semibold text-center">Estado</th>
                <th class="px-6 py-4 font-semibold text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
              <tr v-for="s in students" :key="s.id" class="hover:bg-[var(--color-bg-hover)] transition-colors group">
                <td class="px-6 py-4 font-medium">
                  <div class="flex items-center gap-3">
                    <UserAvatar :name="s.full_name || s.email" size="w-8 h-8" />
                    <div>
                      {{ s.full_name }}
                      <span v-if="s.is_stuck" class="ml-2 inline-flex items-center gap-1 text-xs bg-red-100 text-red-700 px-2.5 py-0.5 rounded-full font-semibold border border-red-200">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        Atascado
                      </span>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 text-[var(--color-text-muted)]">{{ s.email }}</td>
                <td class="px-6 py-4 text-center">
                  <span v-if="s.status === 'active'" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                    Activo
                  </span>
                  <span v-else class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800">
                    {{ s.status }}
                  </span>
                </td>
                <td class="px-6 py-4 text-right">
                  <router-link :to="`/admin/estudiantes/${s.id}`" class="btn btn-secondary py-1.5 px-3 text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                    Ver detalle
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </transition>
  </div>
</template>
