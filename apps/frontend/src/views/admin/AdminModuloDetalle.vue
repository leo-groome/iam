<script setup lang="ts">
import { useRoute } from 'vue-router';
const route = useRoute();
import { cursos, findCurso } from "@/lib/mock";

const id = route.params.id as string;
const modId = route.params.modId as string;


const isNew = modId === 'nuevo';
const curso = findCurso(id);
const mod = !isNew ? curso?.modulos.find(m => m.id === modId) : null;
</script>

<template>
  <div class="page-container">


  <router-link :to="`/admin/cursos/${id}`" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">← Curso</router-link>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ isNew ? "Nuevo módulo" : `Editar: ${mod?.title}` }}</h1>
    <button class="btn btn-primary">Guardar</button>
  </header>

  <div class="card p-6 mb-6 space-y-4">
    <div>
      <label class="label">Título</label>
      <input class="input" minlength="3" maxlength="60" :value="mod?.title ?? ''" />
    </div>
    <div>
      <label class="label">Descripción</label>
      <textarea class="input">{{ mod?.description ?? '' }}</textarea>
    </div>
  </div>

  <section v-if="!isNew && mod">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-xl font-bold">Temas</h2>
      <router-link :to="`/admin/cursos/${id}/modulos/${modId}/temas/nuevo`" class="btn btn-secondary">+ Agregar tema</router-link>
    </div>
    <div class="space-y-3">
      <div v-for="(t, i) in mod.temas" :key="t.id" class="card p-4 flex items-center justify-between gap-3">
        <div>
          <p class="text-xs text-[var(--color-text-muted)]">Tema {{ i + 1 }} · {{ t.type }}</p>
          <p class="font-semibold">{{ t.title }}</p>
          <p class="text-sm text-[var(--color-text-muted)]">{{ t.duration }} · {{ t.hasExam ? 'Con examen' : 'Sin examen' }}</p>
        </div>
        <router-link :to="`/admin/cursos/${id}/modulos/${modId}/temas/${t.id}`" class="btn btn-secondary">Editar</router-link>
      </div>
    </div>
  </section>


  </div>
</template>
