<script setup lang="ts">
import { useRoute } from 'vue-router';
const route = useRoute();
import { cursos, preguntasMock } from "@/lib/mock";

const id = route.params.id as string;
const modId = route.params.modId as string;
const temaId = route.params.temaId as string;
</script>

<template>
  <div class="page-container">


  <router-link :to="`/admin/cursos/${id}/modulos/${modId}/temas/${temaId}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Tema</router-link>
  <header class="flex items-center justify-between mb-6">
    <div>
      <h1 class="text-2xl font-bold">Banco de preguntas</h1>
      <p class="text-[var(--color-text-muted)]">{{ preguntasMock.length }} preguntas activas</p>
    </div>
    <router-link :to="`/admin/cursos/${id}/modulos/${modId}/temas/${temaId}/preguntas/nueva`" class="btn btn-primary">+ Agregar pregunta</router-link>
  </header>

  <div class="card p-6 mb-6">
    <label class="label">% mínimo para aprobar</label>
    <div class="flex items-center gap-3">
      <input type="number" class="input max-w-32" min="50" max="100" value="70" />
      <p class="text-sm text-[var(--color-text-muted)]">Mínimo 50, máximo 100. Default 70.</p>
    </div>
  </div>

  <div class="space-y-3">
    <div v-for="(p, i) in preguntasMock" :key="p.id" class="card p-5">
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <p class="text-xs text-[var(--color-text-muted)] mb-1">Pregunta {{ i + 1 }}</p>
          <p class="font-semibold">{{ p.enunciado }}</p>
          <ul class="mt-3 space-y-1 text-sm">
            <li v-for="(opt, oi) in p.opciones" :key="oi" :class="['flex items-center gap-2', oi === p.correcta ? 'text-emerald-700 font-medium' : 'text-[var(--color-text-muted)]']">
              <span>{{ oi === p.correcta ? '✓' : '○' }}</span>
              <span>{{ opt }}</span>
            </li>
          </ul>
        </div>
        <router-link :to="`/admin/cursos/${id}/modulos/${modId}/temas/${temaId}/preguntas/${p.id}`" class="btn btn-secondary">Editar</router-link>
      </div>
    </div>
  </div>


  </div>
</template>
