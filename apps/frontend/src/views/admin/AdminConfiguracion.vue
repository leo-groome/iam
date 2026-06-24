<script setup lang="ts">
// TODO: endpoint backend pendiente (/api/v1/config o similar)
</script>

<template>
  <div class="page-container pb-12">

    <header class="mb-6">
      <h1 class="text-3xl font-bold">Configuración</h1>
      <p class="text-[var(--color-text-muted)]">Ajustes generales de la plataforma y funcionamiento del sistema.</p>
    </header>


    <div class="grid gap-6 max-w-3xl">
      
      <!-- Control de Acceso -->
      <div class="card p-6 border-l-4 border-l-[var(--color-primary)]">
        <h2 class="font-semibold text-lg mb-1">Control de Acceso</h2>
        <p class="text-sm text-[var(--color-text-muted)] mb-5">Administra quién puede entrar y usar la plataforma educativa.</p>
        
        <div class="space-y-4">
          <label class="flex items-center justify-between p-3 bg-[var(--color-app-bg)] rounded border border-[var(--color-border)]">
            <div>
              <span class="text-sm font-bold block">Permitir nuevos registros</span>
              <span class="text-xs text-[var(--color-text-muted)]">Si se desactiva, nadie nuevo podrá crear cuenta.</span>
            </div>
            <input type="checkbox" checked class="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
          </label>

          <label class="flex items-center justify-between p-3 bg-rose-50 border border-rose-200 rounded">
            <div>
              <span class="text-sm font-bold text-rose-900 block">Modo Mantenimiento</span>
              <span class="text-xs text-rose-700">Bloquea el acceso a todos los estudiantes (muestra mensaje de "En mantenimiento").</span>
            </div>
            <input type="checkbox" class="w-5 h-5 accent-rose-600 cursor-pointer" />
          </label>
        </div>
      </div>

      <!-- Ajustes Académicos Globales -->
      <div class="card p-6">
        <h2 class="font-semibold text-lg mb-1">Ajustes Académicos Globales</h2>
        <p class="text-sm text-[var(--color-text-muted)] mb-5">Reglas por defecto que aplican a todos los cursos nuevos.</p>
        
        <div class="space-y-5">
          <label class="flex items-center justify-between">
            <div>
              <span class="text-sm font-medium block">Emisión automática de certificados</span>
              <span class="text-xs text-[var(--color-text-muted)]">Generar y enviar el PDF en cuanto aprueban el examen final.</span>
            </div>
            <input type="checkbox" checked class="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
          </label>

          <div class="pt-2 border-t border-[var(--color-border)]">
            <label class="label">Puntaje mínimo global de aprobación</label>
            <p class="text-xs text-[var(--color-text-muted)] mb-2">Este valor se usará si un curso no tiene un puntaje específico configurado.</p>
            <div class="flex items-center gap-3">
              <input type="number" class="input w-24 text-center font-bold" value="80" min="0" max="100" />
              <span class="text-sm font-medium">/ 100 puntos</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Branding -->
      <div class="card p-6">
        <h2 class="font-semibold text-lg mb-1">Branding e Identidad</h2>
        <p class="text-sm text-[var(--color-text-muted)] mb-4">Logo y colores que ven los estudiantes dentro de sus cursos.</p>
        <div class="grid sm:grid-cols-2 gap-6">
          <div>
            <label class="label">Logo de la plataforma</label>
            <div class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-6 text-center text-sm text-[var(--color-text-muted)] hover:border-[var(--color-primary)] transition-colors cursor-pointer relative bg-[var(--color-app-bg)]">
              <input type="file" accept="image/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
              <div class="mx-auto w-10 h-10 rounded-full bg-[var(--color-primary-soft)] text-[var(--color-primary)] flex items-center justify-center mb-2">
                <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
              </div>
              Haz clic para subir logo
            </div>
          </div>
          <div>
            <label class="label">Color primario</label>
            <div class="flex items-center gap-3">
              <input type="color" value="#1448E0" class="w-12 h-12 rounded-lg border border-[var(--color-border)] cursor-pointer p-1 bg-white" />
              <input class="input flex-1 font-mono text-sm" value="#1448E0" />
            </div>
            <p class="text-xs text-[var(--color-text-muted)] mt-2">Afecta botones y acentos visuales.</p>
          </div>
        </div>
      </div>


      <!-- Legal -->
      <div class="card p-6">
        <h2 class="font-semibold text-lg mb-1">Textos Legales</h2>
        <p class="text-sm text-[var(--color-text-muted)] mb-4">Términos y política de privacidad que los estudiantes deben aceptar.</p>
        <div class="flex flex-col sm:flex-row gap-3">
          <button class="btn btn-secondary flex-1">Editar Términos de Uso</button>
          <button class="btn btn-secondary flex-1">Editar Políticas de Privacidad</button>
        </div>
      </div>

      <div class="flex justify-center pt-4">
        <button class="btn btn-primary px-8">Guardar toda la configuración</button>
      </div>

    </div>

  </div>
</template>
