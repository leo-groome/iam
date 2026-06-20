<script setup lang="ts">
import { useRoute } from 'vue-router';
const route = useRoute();
import { cursos, preguntasMock } from "@/lib/mock";

const id = route.params.id as string;
const modId = route.params.modId as string;
const temaId = route.params.temaId as string;
const qId = route.params.qId as string;


const isNew = qId === 'nueva';
const pregunta = !isNew ? preguntasMock.find(p => p.id === qId) : null;
const opts = pregunta?.opciones ?? ["", "", ""];
const correctIdx = pregunta?.correcta ?? 0;
const backUrl = `/admin/cursos/${id}/modulos/${modId}/temas/${temaId}/preguntas`;
</script>

<template>
  <div class="page-container">


  <router-link :to="backUrl" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Banco de preguntas</router-link>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Nueva pregunta" : "Editar pregunta" }}</h1>
    <div class="flex gap-2">
      <router-link :to="backUrl" class="btn btn-secondary">Cancelar</router-link>
      <button class="btn btn-primary">Guardar</button>
    </div>
  </header>

  <div class="card p-6 space-y-5 max-w-2xl">
    <div>
      <label class="label">Enunciado</label>
      <textarea class="input min-h-24" maxlength="300" placeholder="Escribe la pregunta">{{ pregunta?.enunciado ?? '' }}</textarea>
      <p class="help">5–300 caracteres.</p>
    </div>
    <div>
      <label class="label">Opciones de respuesta</label>
      <p class="help mb-3">Marca cuál es la correcta (3 a 5 opciones).</p>
      <div class="space-y-2">
        <div v-for="(opt, i) in opts" :key="i" class="flex items-center gap-3">
          <input type="radio" name="correcta" :checked="i === correctIdx" class="w-5 h-5 accent-[var(--color-primary)]" />
          <input class="input flex-1" maxlength="150" :value="opt" :placeholder="`Opción ${i + 1}`" />
          <button class="text-[var(--color-text-muted)] hover:text-[var(--color-error)]" aria-label="Eliminar">✕</button>
        </div>
      </div>
      <button class="btn btn-ghost mt-3 text-sm">+ Agregar opción</button>
    </div>
  </div>


  </div>
</template>
