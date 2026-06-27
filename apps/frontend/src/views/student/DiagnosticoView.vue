<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

// Placeholder until the admin-authored general diagnostic runner is built.
// New users only land here when GET /api/v1/diagnostic/active reports an active
// diagnostic; otherwise the signup flow skips straight to the catalog.
function skip() {
  router.replace('/catalogo')
}
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-16 text-center">
    <p class="text-sm text-[var(--color-primary)] font-semibold uppercase tracking-wider">
      Diagnóstico inicial
    </p>
    <h1 class="text-3xl font-bold mt-2">Conozcamos tu punto de partida</h1>
    <p class="text-[var(--color-text-muted)] mt-4 leading-relaxed">
      Estamos preparando un breve diagnóstico para ubicarte en el contenido adecuado.
      Muy pronto podrás responderlo aquí mismo.
    </p>

    <button type="button" class="btn btn-primary mt-8" @click="skip">
      Ir al catálogo
    </button>
  </div>
</template>
