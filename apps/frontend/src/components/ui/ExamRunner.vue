<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { apiGet, apiPost, ApiError } from '@/lib/api'
import type { ExamResponse, QuestionOut } from '@/lib/api'

const props = defineProps<{
  topicId: string
  cursoId: string
}>()

// State
const loading = ref(true)
const fetchError = ref<string | null>(null)
const submitError = ref<string | null>(null)
const submitting = ref(false)

const examToken = ref<string>('')
const questions = ref<QuestionOut[]>([])
const minScore = ref<number>(70)

const idx = ref(0)
const answers = ref<Map<string, string>>(new Map())
const selectedOption = ref<string | null>(null)

const result = ref<{ score: number; passed: boolean; min_score: number; message: string } | null>(null)

// Fetch exam on mount
onMounted(async () => {
  try {
    const data = (await apiGet('/api/v1/topics/{topic_id}/exam', {
      params: { topic_id: props.topicId },
    })) as ExamResponse

    examToken.value = data.exam_token
    questions.value = data.questions
    minScore.value = data.min_score
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        window.location.href = '/registro'
        return
      }
      fetchError.value = err.status === 429
        ? 'Demasiados intentos, espera unos minutos.'
        : (err.message || 'No se pudo cargar el examen.')
    } else {
      fetchError.value = 'Error de red. Verifica tu conexion.'
    }
  } finally {
    loading.value = false
  }
})

// Navigation
const currentQuestion = computed(() => questions.value[idx.value])

function next() {
  if (!selectedOption.value || !currentQuestion.value) return
  answers.value.set(currentQuestion.value.id, selectedOption.value)
  selectedOption.value = null

  if (idx.value < questions.value.length - 1) {
    idx.value++
  } else {
    submitExam()
  }
}

// Submit
async function submitExam() {
  submitting.value = true
  submitError.value = null

  const answerPayload = Array.from(answers.value.entries()).map(([question_id, option_id]) => ({
    question_id,
    option_id,
  }))

  try {
    const res = (await apiPost('/api/v1/topics/{topic_id}/exam/submit', {
      params: { topic_id: props.topicId },
      body: {
        exam_token: examToken.value,
        answers: answerPayload,
      },
    })) as { score: number; passed: boolean; min_score: number; message: string }

    result.value = res
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        window.location.href = '/registro'
        return
      }
      if (err.status === 429) {
        submitError.value = 'Demasiados intentos, espera unos minutos.'
      } else if (err.status === 422) {
        submitError.value = 'Error de validacion. Vuelve a intentarlo.'
      } else {
        submitError.value = err.message || 'Error al enviar el examen.'
      }
    } else {
      submitError.value = 'Error de red al enviar. Intenta de nuevo.'
    }
    idx.value = questions.value.length - 1
    selectedOption.value = null
  } finally {
    submitting.value = false
  }
}

// CTAs
const repasoHref = computed(
  () => `/curso/${props.cursoId}/tema/${props.topicId}?repaso=1`,
)
const resultadoHref = computed(() => {
  const s = result.value?.score ?? 0
  return `/curso/${props.cursoId}/tema/${props.topicId}/resultado?score=${s}&pass=1`
})

const progressPct = computed(() =>
  questions.value.length ? Math.round((idx.value / questions.value.length) * 100) : 0,
)
</script>

<template>
  <!-- Loading skeleton -->
  <div v-if="loading" class="space-y-4 animate-pulse">
    <div class="h-4 bg-[var(--color-primary-soft)] rounded-full w-1/2"></div>
    <div class="h-1.5 bg-[var(--color-primary-soft)] rounded-full"></div>
    <div class="card p-6">
      <div class="h-6 bg-[var(--color-border)] rounded w-3/4 mb-5"></div>
      <div class="space-y-3">
        <div v-for="n in 4" :key="n" class="h-14 bg-[var(--color-border)] rounded-xl"></div>
      </div>
    </div>
  </div>

  <!-- Fetch error -->
  <div v-else-if="fetchError" class="card p-8 text-center">
    <div class="w-16 h-16 mx-auto rounded-full bg-red-100 text-red-600 grid place-items-center mb-4">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M12 9v4"/><path d="M12 17h.01"/>
        <path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z"/>
      </svg>
    </div>
    <h2 class="text-xl font-bold mb-2">No se pudo cargar el examen</h2>
    <p class="text-[var(--color-text-muted)] mb-6">{{ fetchError }}</p>
    <button @click="() => window.location.reload()" class="btn btn-primary">
      Reintentar
    </button>
  </div>

  <!-- Active exam -->
  <div v-else-if="!result">
    <!-- Submit error banner -->
    <div
      v-if="submitError"
      class="mb-4 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3"
    >
      <svg class="shrink-0 mt-0.5" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M12 9v4"/><path d="M12 17h.01"/>
        <path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z"/>
      </svg>
      <span>{{ submitError }}</span>
    </div>

    <!-- Progress bar -->
    <div class="flex items-center justify-between mb-4 text-sm text-[var(--color-text-muted)]">
      <span>Pregunta {{ idx + 1 }} de {{ questions.length }}</span>
      <span>{{ progressPct }}%</span>
    </div>
    <div class="h-1.5 bg-[var(--color-primary-soft)] rounded-full overflow-hidden mb-6">
      <div
        class="h-full bg-[var(--color-primary)] transition-all"
        :style="{ width: progressPct + '%' }"
      ></div>
    </div>

    <!-- Question card -->
    <div v-if="currentQuestion" class="card p-6 mb-6">
      <h2 class="text-xl font-bold mb-5">{{ currentQuestion.enunciado }}</h2>
      <div class="space-y-2">
        <button
          v-for="opt in currentQuestion.options"
          :key="opt.id"
          @click="selectedOption = opt.id"
          :class="[
            'w-full text-left p-4 rounded-xl border-2 transition flex items-center gap-3',
            selectedOption === opt.id
              ? 'border-[var(--color-primary)] bg-[var(--color-primary-soft)]'
              : 'border-[var(--color-border)] bg-white hover:border-[var(--color-primary-soft)]',
          ]"
        >
          <span
            :class="[
              'w-6 h-6 rounded-full border-2 grid place-items-center shrink-0',
              selectedOption === opt.id
                ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-white'
                : 'border-[var(--color-border)]',
            ]"
          >
            <svg
              v-if="selectedOption === opt.id"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
            >
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          </span>
          <span class="font-medium">{{ opt.texto }}</span>
        </button>
      </div>
    </div>

    <!-- Sticky CTA -->
    <div class="fixed bottom-0 left-0 right-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-4 z-20">
      <div class="max-w-3xl mx-auto">
        <button
          @click="next"
          :disabled="!selectedOption || submitting"
          class="btn btn-primary btn-block"
        >
          <span v-if="submitting">Enviando...</span>
          <span v-else-if="idx === questions.length - 1">Enviar respuestas</span>
          <span v-else>Siguiente</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Result card -->
  <div v-else class="card p-8 text-center">
    <!-- Passed -->
    <div v-if="result.passed">
      <div class="w-20 h-20 mx-auto rounded-full bg-emerald-100 text-emerald-600 grid place-items-center mb-4">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M20 6L9 17l-5-5"/>
        </svg>
      </div>
      <h2 class="text-3xl font-bold">Aprobado</h2>
      <p class="text-5xl font-extrabold text-[var(--color-primary)] mt-4">{{ result.score }}</p>
      <p class="text-[var(--color-text-muted)] mt-2">Calificacion minima: {{ result.min_score }}</p>
      <p v-if="result.message" class="text-sm text-[var(--color-text-muted)] mt-1">{{ result.message }}</p>
      <a :href="resultadoHref" class="btn btn-primary btn-block mt-6">
        Continuar al siguiente tema
      </a>
    </div>

    <!-- Failed -->
    <div v-else>
      <div class="w-20 h-20 mx-auto rounded-full bg-amber-100 text-amber-600 grid place-items-center mb-4">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 9v4"/><path d="M12 17h.01"/>
          <path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z"/>
        </svg>
      </div>
      <h2 class="text-2xl font-bold">No esta vez</h2>
      <p class="text-[var(--color-text-muted)] mt-1">Vamos a repasar juntos.</p>
      <p class="text-5xl font-extrabold text-[var(--color-text-muted)] mt-4">{{ result.score }}</p>
      <p class="text-[var(--color-text-muted)] mt-2">Necesitas al menos {{ result.min_score }} para aprobar.</p>
      <p v-if="result.message" class="text-sm text-[var(--color-text-muted)] mt-1">{{ result.message }}</p>
      <a :href="repasoHref" class="btn btn-primary btn-block mt-6">
        Volver a ver el video
      </a>
    </div>
  </div>
</template>
