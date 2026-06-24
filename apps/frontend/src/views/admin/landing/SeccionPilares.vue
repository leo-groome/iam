<template>
  <section class="card p-6 space-y-5">
    <div>
      <h2 class="text-xl font-semibold">Pilares</h2>
      <p class="text-sm text-[var(--color-text-muted)]">Edita los mensajes base de la propuesta formativa.</p>
    </div>

    <div class="grid gap-4 md:grid-cols-3">
      <label v-for="pillar in pillars" :key="pillar.title">
        <span class="label">{{ pillar.title }}</span>
        <textarea class="input min-h-28" :value="pillar.text"></textarea>
      </label>
    </div>

    <div class="flex justify-end">
      <button class="btn btn-primary">Guardar pilares</button>
    </div>
  </section>
</template>

<script setup lang="ts">
const pillars = [
  { title: 'Educar', text: 'Formacion clara, cercana y orientada al servicio.' },
  { title: 'Acompanar', text: 'Procesos humanos sostenidos con cuidado y escucha.' },
  { title: 'Servir', text: 'Acciones concretas para fortalecer a la comunidad.' },
];
</script>
