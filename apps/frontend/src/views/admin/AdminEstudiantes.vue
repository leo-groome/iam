<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { adminService } from '@/services/admin.service'

const students = ref<any[]>([])
const loading = ref(true)
const search = ref('')
const statusFilter = ref('')

async function fetchStudents() {
  loading.value = true
  students.value = (await adminService.getStudents({
    search: search.value || undefined,
    status: statusFilter.value || undefined,
  })) as any[] ?? []
  loading.value = false
}

onMounted(fetchStudents)
watch([search, statusFilter], fetchStudents)
</script>

<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">Estudiantes</h1>
    <div class="flex gap-4 mb-4">
      <input v-model="search" type="text" placeholder="Buscar por nombre..." class="border rounded px-3 py-2 flex-1" />
      <select v-model="statusFilter" class="border rounded px-3 py-2">
        <option value="">Todos los estados</option>
        <option value="active">Activo</option>
        <option value="inactive">Inactivo</option>
        <option value="stuck">Atascado</option>
      </select>
    </div>
    <div v-if="loading" class="text-center py-8 text-gray-500">Cargando...</div>
    <table v-else class="w-full border-collapse">
      <thead>
        <tr class="bg-gray-100">
          <th class="text-left p-3 border-b">Nombre</th>
          <th class="text-left p-3 border-b">Email</th>
          <th class="text-left p-3 border-b">Estado</th>
          <th class="text-left p-3 border-b">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in students" :key="s.id" class="border-b hover:bg-gray-50">
          <td class="p-3">
            {{ s.full_name }}
            <span v-if="s.is_stuck" class="ml-2 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">⚠ Atascado</span>
          </td>
          <td class="p-3">{{ s.email }}</td>
          <td class="p-3">
            <span :class="s.status === 'active' ? 'text-green-600' : 'text-gray-400'">{{ s.status }}</span>
          </td>
          <td class="p-3">
            <router-link :to="`/admin/estudiantes/${s.id}`" class="text-blue-600 hover:underline">Ver detalle</router-link>
          </td>
        </tr>
        <tr v-if="students.length === 0">
          <td colspan="4" class="p-6 text-center text-gray-400">No se encontraron estudiantes.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
