<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminService } from '@/services/admin.service'

const courses = ref<any[]>([])
const selectedCourseId = ref('')
const passRates = ref<any[]>([])
const loadingPassRate = ref(false)

const API_BASE = import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000'

function exportReport(type: string) {
  window.open(`${API_BASE}/api/v1/admin/reports/export?type=${type}`, '_blank')
}

async function loadPassRate() {
  if (!selectedCourseId.value) return
  loadingPassRate.value = true
  passRates.value = (await adminService.getTopicPassRate(selectedCourseId.value)) as any[] ?? []
  loadingPassRate.value = false
}

onMounted(async () => {
  courses.value = (await adminService.getCourses()) as any[] ?? []
})
</script>

<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">Reportes</h1>

    <section class="mb-8">
      <h2 class="text-lg font-semibold mb-3">Exportar Datos</h2>
      <div class="flex gap-3 flex-wrap">
        <button @click="exportReport('enrollments')" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          Exportar Inscripciones (CSV)
        </button>
        <button @click="exportReport('completions')" class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
          Exportar Finalizaciones (CSV)
        </button>
        <button @click="exportReport('exam_attempts')" class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
          Exportar Intentos de Examen (CSV)
        </button>
      </div>
    </section>

    <section>
      <h2 class="text-lg font-semibold mb-3">Tasa de Aprobación por Tema</h2>
      <div class="flex gap-3 mb-4">
        <select v-model="selectedCourseId" class="border rounded px-3 py-2 flex-1">
          <option value="">Seleccionar curso...</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.title }}</option>
        </select>
        <button @click="loadPassRate" :disabled="!selectedCourseId" class="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-800 disabled:opacity-50">
          Ver Reporte
        </button>
      </div>
      <div v-if="loadingPassRate" class="text-center py-4 text-gray-500">Cargando...</div>
      <table v-else-if="passRates.length" class="w-full border-collapse">
        <thead>
          <tr class="bg-gray-100">
            <th class="text-left p-3 border-b">Tema</th>
            <th class="text-left p-3 border-b">Módulo</th>
            <th class="text-left p-3 border-b">Tasa de Aprobación</th>
            <th class="text-left p-3 border-b">Intentos</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in passRates" :key="r.topic_id" class="border-b">
            <td class="p-3">{{ r.topic_title }}</td>
            <td class="p-3">{{ r.module_title }}</td>
            <td class="p-3">
              <span :class="r.pass_rate >= 0.7 ? 'text-green-600' : 'text-red-500'">{{ Math.round(r.pass_rate * 100) }}%</span>
            </td>
            <td class="p-3">{{ r.total_attempts }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else-if="selectedCourseId" class="text-gray-400 text-center py-4">Sin datos para este curso.</p>
    </section>
  </div>
</template>
