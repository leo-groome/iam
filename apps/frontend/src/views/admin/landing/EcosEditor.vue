<template>
  <section class="card p-6 space-y-5">
    <div>
      <h2 class="text-xl font-semibold">Ecos</h2>
      <p class="text-sm text-[var(--color-text-muted)]">Gestiona testimonios o mensajes breves para publicar.</p>
    </div>

    <div class="space-y-4">
      <article v-for="echo in echoes" :key="echo.author" class="rounded-lg border border-[var(--color-border)] p-4">
        <label>
          <span class="label">Autor</span>
          <input class="input" :value="echo.author" />
        </label>
        <label class="mt-3 block">
          <span class="label">Mensaje</span>
          <textarea class="input min-h-24" :value="echo.message"></textarea>
        </label>
      </article>
    </div>

    <div class="flex justify-end gap-3">
      <button class="btn btn-secondary">Agregar eco</button>
      <button class="btn btn-primary">Guardar ecos</button>
    </div>
  </section>
</template>

<script setup lang="ts">
const echoes = [
  { author: 'Participante', message: 'La formacion me ayudo a servir mejor en mi comunidad.' },
  { author: 'Coordinadora', message: 'El proceso facilita seguimiento y acompanamiento constante.' },
];
</script>
