<template>
  <section class="card p-6 space-y-5">
    <div>
      <h2 class="text-xl font-semibold">Quienes somos</h2>
      <p class="text-sm text-[var(--color-text-muted)]">Actualiza la descripcion institucional de la landing.</p>
    </div>

    <div class="grid gap-4">
      <label>
        <span class="label">Encabezado</span>
        <input class="input" value="Misioneras al servicio de la formacion" />
      </label>
      <label>
        <span class="label">Descripcion</span>
        <textarea class="input min-h-36">Somos una comunidad dedicada a formar, acompanar y servir.</textarea>
      </label>
    </div>

    <div class="flex justify-end">
      <button class="btn btn-primary">Guardar seccion</button>
    </div>
  </section>
</template>
