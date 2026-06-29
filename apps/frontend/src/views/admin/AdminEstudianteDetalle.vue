<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminService } from '@/services/admin.service'

const route = useRoute()
const router = useRouter()
const student = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  student.value = await adminService.getStudentDetail(route.params.id as string)
  loading.value = false
})
</script>

<template>
  <div class="p-6">
    <button @click="router.back()" class="mb-4 text-blue-600 hover:underline">← Volver</button>
    <div v-if="loading" class="text-center py-8 text-gray-500">Cargando...</div>
    <template v-else-if="student">
      <div class="flex items-center gap-4 mb-6">
        <img :src="`https://api.dicebear.com/9.x/notionists-neutral/svg?seed=${encodeURIComponent(student.full_name || student.email || 'avatar')}`" alt="Avatar" class="w-16 h-16 rounded-full bg-blue-100 shrink-0" />
        <div>
          <h1 class="text-2xl font-bold">{{ student.full_name }}</h1>
          <p class="text-gray-500">{{ student.email }}</p>
        </div>
      </div>

      <h2 class="text-lg font-semibold mb-3">Cursos Inscritos</h2>
      <table class="w-full border-collapse mb-8">
        <thead>
          <tr class="bg-gray-100">
            <th class="text-left p-3 border-b">Curso</th>
            <th class="text-left p-3 border-b">Progreso</th>
            <th class="text-left p-3 border-b">Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in (student.enrollments ?? [])" :key="e.id" class="border-b">
            <td class="p-3">{{ e.course_title }}</td>
            <td class="p-3">{{ e.progress_cached ?? e.progress_percentage ?? 0 }}%</td>
            <td class="p-3">{{ e.status ?? (e.completed_at ? 'completado' : 'en_progreso') }}</td>
          </tr>
          <tr v-if="!(student.enrollments?.length)">
            <td colspan="3" class="p-6 text-center text-gray-400">Sin inscripciones.</td>
          </tr>
        </tbody>
      </table>

      <h2 class="text-lg font-semibold mb-3">Intentos de Examen</h2>
      <table class="w-full border-collapse">
        <thead>
          <tr class="bg-gray-100">
            <th class="text-left p-3 border-b">Tema</th>
            <th class="text-left p-3 border-b">Puntuación</th>
            <th class="text-left p-3 border-b">Resultado</th>
            <th class="text-left p-3 border-b">Fecha</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in (student.exam_attempts ?? [])" :key="a.id" class="border-b">
            <td class="p-3">{{ a.topic_title ?? a.module_title ?? 'Diagnóstico' }}</td>
            <td class="p-3">{{ a.score }}%</td>
            <td class="p-3">
              <span :class="a.passed ? 'text-green-600' : 'text-red-500'">{{ a.passed ? 'Aprobado' : 'Reprobado' }}</span>
            </td>
            <td class="p-3">{{ new Date(a.created_at).toLocaleDateString('es-MX') }}</td>
          </tr>
          <tr v-if="!(student.exam_attempts?.length)">
            <td colspan="4" class="p-6 text-center text-gray-400">Sin intentos de examen.</td>
          </tr>
        </tbody>
      </table>
    </template>
    <div v-else class="text-center py-8 text-gray-400">Estudiante no encontrado.</div>
  </div>
</template>
