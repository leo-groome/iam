<script setup lang="ts">
import { ref, computed } from 'vue';

type Pregunta = { id: string; enunciado: string; opciones: string[]; correcta: number };

const props = defineProps<{
  preguntas: Pregunta[];
  cursoId: string;
  temaId: string;
  minPercent: number;
}>();

function shuffle<T>(arr: T[]): T[] {
  return [...arr].sort(() => Math.random() - 0.5);
}

const order = ref(shuffle(props.preguntas.map((_, i) => i)));
const optionOrders = ref(props.preguntas.map(p => shuffle(p.opciones.map((_, i) => i))));

const idx = ref(0);
const respuestas = ref<number[]>([]);
const finished = ref(false);

const current = computed(() => props.preguntas[order.value[idx.value]]);
const currentOptions = computed(() => {
  const realIdx = order.value[idx.value];
  return optionOrders.value[realIdx].map(i => ({ label: props.preguntas[realIdx].opciones[i], realIndex: i }));
});

const selected = ref<number | null>(null);

function next() {
  if (selected.value === null) return;
  respuestas.value.push(selected.value);
  selected.value = null;
  if (idx.value < props.preguntas.length - 1) {
    idx.value++;
  } else {
    finished.value = true;
  }
}

const score = computed(() => {
  let correct = 0;
  respuestas.value.forEach((ans, i) => {
    const realIdx = order.value[i];
    if (ans === props.preguntas[realIdx].correcta) correct++;
  });
  return Math.round((correct / props.preguntas.length) * 100);
});

const aprobado = computed(() => score.value >= props.minPercent);
</script>

<template>
  <div v-if="!finished">
    <div class="flex items-center justify-between mb-4 text-sm text-[var(--color-text-muted)]">
      <span>Pregunta {{ idx + 1 }} de {{ preguntas.length }}</span>
      <span>{{ Math.round(((idx) / preguntas.length) * 100) }}%</span>
    </div>
    <div class="h-1.5 bg-[var(--color-primary-soft)] rounded-full overflow-hidden mb-6">
      <div class="h-full bg-[var(--color-primary)] transition-all" :style="{ width: ((idx) / preguntas.length * 100) + '%' }"></div>
    </div>

    <div class="card p-6 mb-6">
      <h2 class="text-xl font-bold mb-5">{{ current.enunciado }}</h2>
      <div class="space-y-2">
        <button
          v-for="(opt, i) in currentOptions"
          :key="i"
          @click="selected = opt.realIndex"
          :class="[
            'w-full text-left p-4 rounded-xl border-2 transition flex items-center gap-3',
            selected === opt.realIndex
              ? 'border-[var(--color-primary)] bg-[var(--color-primary-soft)]'
              : 'border-[var(--color-border)] bg-white hover:border-[var(--color-primary-soft)]'
          ]"
        >
          <span :class="[
            'w-6 h-6 rounded-full border-2 grid place-items-center shrink-0',
            selected === opt.realIndex ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-white' : 'border-[var(--color-border)]'
          ]">
            <svg v-if="selected === opt.realIndex" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
          </span>
          <span class="font-medium">{{ opt.label }}</span>
        </button>
      </div>
    </div>

    <div class="fixed bottom-0 left-0 right-0 bg-[var(--color-surface)] border-t border-[var(--color-border)] p-4 z-20">
      <div class="max-w-3xl mx-auto">
        <button @click="next" :disabled="selected === null" class="btn btn-primary btn-block">
          {{ idx === preguntas.length - 1 ? 'Enviar respuestas' : 'Siguiente' }}
        </button>
      </div>
    </div>
  </div>

  <div v-else class="card p-8 text-center">
    <div v-if="aprobado">
      <div class="w-20 h-20 mx-auto rounded-full bg-emerald-100 text-emerald-600 grid place-items-center mb-4">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
      </div>
      <h2 class="text-3xl font-bold">¡Aprobado!</h2>
      <p class="text-5xl font-extrabold text-[var(--color-primary)] mt-4">{{ score }}</p>
      <p class="text-[var(--color-text-muted)] mt-2">Calificación mínima: {{ minPercent }}</p>
      <a :href="`/curso/${cursoId}/tema/${temaId}/resultado?score=${score}&pass=1`" class="btn btn-primary btn-block mt-6">
        Continuar al siguiente tema
      </a>
    </div>
    <div v-else>
      <div class="w-20 h-20 mx-auto rounded-full bg-amber-100 text-amber-600 grid place-items-center mb-4">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z"/></svg>
      </div>
      <h2 class="text-2xl font-bold">No esta vez</h2>
      <p class="text-[var(--color-text-muted)] mt-1">Vamos a repasar juntos.</p>
      <p class="text-5xl font-extrabold text-[var(--color-text-muted)] mt-4">{{ score }}</p>
      <p class="text-[var(--color-text-muted)] mt-2">Necesitas al menos {{ minPercent }} para aprobar.</p>
      <a :href="`/curso/${cursoId}/tema/${temaId}?repaso=1`" class="btn btn-primary btn-block mt-6">
        Volver a ver el video
      </a>
    </div>
  </div>
</template>
