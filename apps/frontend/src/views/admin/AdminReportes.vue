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
  <div class="max-w-7xl mx-auto space-y-6">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-[var(--color-text)]">Reportes</h1>
        <p class="text-[var(--color-text-muted)] mt-1">Exportación de datos y análisis de rendimiento</p>
      </div>
    </header>

    <div class="grid lg:grid-cols-3 gap-6">
      <div class="card p-6 lg:col-span-1 space-y-4 h-fit">
        <div>
          <h2 class="text-lg font-bold">Exportar Datos</h2>
          <p class="text-sm text-[var(--color-text-muted)] mt-1 mb-4">Descarga reportes crudos en formato CSV para análisis externo.</p>
        </div>
        <div class="flex flex-col gap-3">
          <button @click="exportReport('enrollments')" class="btn w-full justify-center bg-blue-600 text-white hover:bg-blue-700 border-transparent shadow-sm">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            Exportar Inscripciones
          </button>
          <button @click="exportReport('completions')" class="btn w-full justify-center bg-emerald-600 text-white hover:bg-emerald-700 border-transparent shadow-sm">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            Exportar Finalizaciones
          </button>
          <button @click="exportReport('exam_attempts')" class="btn w-full justify-center bg-purple-600 text-white hover:bg-purple-700 border-transparent shadow-sm">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            Exportar Exámenes
          </button>
        </div>
      </div>

      <div class="card lg:col-span-2 overflow-hidden flex flex-col">
        <div class="p-6 border-b border-[var(--color-border)]">
          <h2 class="text-lg font-bold mb-4">Tasa de Aprobación por Tema</h2>
          <div class="flex gap-3">
            <select v-model="selectedCourseId" class="input flex-1">
              <option value="">Seleccionar curso para analizar...</option>
              <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.title }}</option>
            </select>
            <button @click="loadPassRate" :disabled="!selectedCourseId" class="btn btn-primary whitespace-nowrap">
              Cargar Reporte
            </button>
          </div>
        </div>
        
        <div class="flex-1 p-0 overflow-x-auto">
          <div v-if="loadingPassRate" class="text-center py-12 text-[var(--color-text-muted)]">Analizando datos...</div>
          <table v-else-if="passRates.length" class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-[var(--color-bg-hover)] border-b border-[var(--color-border)] text-sm">
                <th class="px-6 py-4 font-semibold">Tema</th>
                <th class="px-6 py-4 font-semibold">Módulo</th>
                <th class="px-6 py-4 font-semibold text-center">Aprobación</th>
                <th class="px-6 py-4 font-semibold text-center">Intentos</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--color-border)]">
              <tr v-for="r in passRates" :key="r.topic_id" class="hover:bg-[var(--color-bg-hover)] transition-colors">
                <td class="px-6 py-4 font-medium">{{ r.topic_title }}</td>
                <td class="px-6 py-4 text-[var(--color-text-muted)]">{{ r.module_title }}</td>
                <td class="px-6 py-4 text-center">
                  <div class="inline-flex items-center justify-center px-2 py-1 rounded-full text-sm font-semibold"
                    :class="r.pass_rate >= 0.7 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
                    {{ Math.round(r.pass_rate * 100) }}%
                  </div>
                </td>
                <td class="px-6 py-4 text-center font-medium">{{ r.total_attempts }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else-if="selectedCourseId" class="text-[var(--color-text-muted)] text-center py-12">
            No hay suficientes datos de evaluación para este curso.
          </div>
          <div v-else class="text-[var(--color-text-muted)] text-center py-12 flex flex-col items-center">
            <svg class="w-12 h-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            Selecciona un curso para ver sus métricas de desempeño.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
