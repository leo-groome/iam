<template>
  <section class="card p-6 space-y-5">
    <div>
      <h2 class="text-xl font-semibold">Inicio</h2>
      <p class="text-sm text-[var(--color-text-muted)]">Contenido principal de bienvenida para la landing.</p>
    </div>

    <div class="grid gap-4">
      <label>
        <span class="label">Titulo principal</span>
        <input class="input" value="Formacion para servir con amor" />
      </label>
      <label>
        <span class="label">Texto destacado</span>
        <textarea class="input min-h-32">Acompana procesos de formacion, servicio y crecimiento comunitario.</textarea>
      </label>
    </div>

    <div class="flex justify-end">
      <button class="btn btn-primary">Guardar inicio</button>
    </div>
  </section>
</template>
