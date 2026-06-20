<script setup lang="ts">
import { cursos } from "@/lib/mock";

const completados = cursos.filter(c => c.progress === 100);
</script>

<template>
  <h1 class="text-3xl font-bold mb-6">Mi perfil</h1>

  <div class="card p-6 mb-6 flex items-center gap-4">
    <div class="w-16 h-16 rounded-full bg-[var(--color-primary)] text-white grid place-items-center text-2xl font-bold">A</div>
    <div>
      <p class="font-bold text-lg">Alex Hernández</p>
      <p class="text-[var(--color-text-muted)] text-sm">alex@correo.com</p>
      <p class="text-[var(--color-text-muted)] text-xs mt-1">Edad: 28 años</p>
    </div>
  </div>

  <h2 class="text-lg font-semibold mb-3">Mis certificados</h2>
  <div v-if="completados.length === 0" class="card p-8 text-center text-[var(--color-text-muted)]">
    Aún no tienes certificados. ¡Completa tu primer curso!
  </div>
  <div v-else class="space-y-3 mb-8">
    <router-link v-for="c in completados" :key="c.id" :to="`/curso/${c.id}/certificado`" class="card p-4 flex items-center gap-3 hover:border-[var(--color-primary)] transition">
      <div class="w-12 h-12 rounded-xl bg-[var(--color-primary-soft)] text-[var(--color-primary)] grid place-items-center text-xl">🎓</div>
      <div class="flex-1 min-w-0">
        <p class="font-semibold truncate">{{ c.title }}</p>
        <p class="text-sm text-[var(--color-text-muted)]">Completado</p>
      </div>
      <span class="text-[var(--color-primary)]">→</span>
    </router-link>
  </div>

  <router-link to="/" class="btn btn-secondary btn-block">Cerrar sesión</router-link>
</template>
