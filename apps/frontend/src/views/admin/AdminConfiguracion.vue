<script setup lang="ts">
import { ref } from 'vue';

// TODO: endpoint backend pendiente (/api/v1/config o similar)
const activeTab = ref('general');

const formData = ref({
  // General
  platform_name: 'IAM de la vida',
  support_email: 'support@iamdelavida.com',
  maintenance_mode: false,
  
  // Acceso
  allow_registration: true,
  default_role: 'student',
  require_email_verification: true,
  
  // Académico
  global_pass_score: 80,
  auto_certificate: true,
  max_attempts: 3,
  
  // Branding
  primary_color: '#1448E0',
});

const isSaving = ref(false);

const saveConfig = async () => {
  isSaving.value = true;
  // MOCK: await api.post('/config', formData.value)
  setTimeout(() => {
    isSaving.value = false;
  }, 800);
};
</script>

<template>
  <div class="max-w-7xl mx-auto space-y-6">
    <header class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-[var(--color-text)]">Configuración del Entorno</h1>
        <p class="text-[var(--color-text-muted)] mt-1">Ajustes globales, variables de entorno y preferencias del sistema.</p>
      </div>
      <button @click="saveConfig" :disabled="isSaving" class="btn btn-primary">
        <svg v-if="!isSaving" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
        <svg v-else class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        {{ isSaving ? 'Guardando...' : 'Guardar Cambios' }}
      </button>
    </header>

    <div class="flex flex-col md:flex-row gap-8 items-start">
      <!-- Menú Lateral -->
      <nav class="w-full md:w-64 flex flex-col gap-1 shrink-0">
        <button @click="activeTab = 'general'" :class="['text-left px-4 py-2.5 rounded-lg font-medium text-sm transition-colors', activeTab === 'general' ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)]']">
          General e Institución
        </button>
        <button @click="activeTab = 'access'" :class="['text-left px-4 py-2.5 rounded-lg font-medium text-sm transition-colors', activeTab === 'access' ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)]']">
          Acceso y Registro
        </button>
        <button @click="activeTab = 'academic'" :class="['text-left px-4 py-2.5 rounded-lg font-medium text-sm transition-colors', activeTab === 'academic' ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)]']">
          Reglas Académicas
        </button>
        <button @click="activeTab = 'branding'" :class="['text-left px-4 py-2.5 rounded-lg font-medium text-sm transition-colors', activeTab === 'branding' ? 'bg-[var(--color-primary-soft)] text-[var(--color-primary)]' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-hover)]']">
          Branding e Identidad
        </button>
      </nav>

      <!-- Área de Configuración -->
      <div class="flex-1 w-full space-y-6">
        
        <!-- GENERAL -->
        <div v-show="activeTab === 'general'" class="card p-6 space-y-6 animate-fade-in">
          <div>
            <h2 class="text-lg font-bold mb-1">Información General</h2>
            <p class="text-sm text-[var(--color-text-muted)]">Datos principales de la plataforma.</p>
          </div>
          <div class="space-y-4">
            <div>
              <label class="label">Nombre de la Plataforma</label>
              <input type="text" v-model="formData.platform_name" class="input" />
            </div>
            <div>
              <label class="label">Correo de Soporte Técnico</label>
              <input type="email" v-model="formData.support_email" class="input" />
            </div>
            <div class="pt-4 border-t border-[var(--color-border)]">
              <label class="flex items-center justify-between p-4 bg-rose-50 border border-rose-200 rounded-lg">
                <div>
                  <span class="text-sm font-bold text-rose-900 block">Modo Mantenimiento</span>
                  <span class="text-xs text-rose-700">Bloquea el acceso a todos los estudiantes (muestra mensaje de "En mantenimiento").</span>
                </div>
                <input type="checkbox" v-model="formData.maintenance_mode" class="w-5 h-5 accent-rose-600 cursor-pointer" />
              </label>
            </div>
          </div>
        </div>

        <!-- ACCESO -->
        <div v-show="activeTab === 'access'" class="card p-6 space-y-6 animate-fade-in">
          <div>
            <h2 class="text-lg font-bold mb-1">Control de Acceso</h2>
            <p class="text-sm text-[var(--color-text-muted)]">Gestiona cómo entran los usuarios a la plataforma.</p>
          </div>
          <div class="space-y-4">
            <label class="flex items-center justify-between p-4 bg-[var(--color-app-bg)] rounded-lg border border-[var(--color-border)]">
              <div>
                <span class="text-sm font-bold block">Permitir nuevos registros públicos</span>
                <span class="text-xs text-[var(--color-text-muted)]">Si se desactiva, los administradores tendrán que crear las cuentas manualmente.</span>
              </div>
              <input type="checkbox" v-model="formData.allow_registration" class="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
            </label>
            
            <label class="flex items-center justify-between p-4 bg-[var(--color-app-bg)] rounded-lg border border-[var(--color-border)]">
              <div>
                <span class="text-sm font-bold block">Requerir verificación de correo</span>
                <span class="text-xs text-[var(--color-text-muted)]">Obligar a los usuarios a confirmar su email antes de acceder al contenido.</span>
              </div>
              <input type="checkbox" v-model="formData.require_email_verification" class="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
            </label>
            
            <div>
              <label class="label">Rol por defecto para nuevos usuarios</label>
              <select v-model="formData.default_role" class="input">
                <option value="student">Estudiante</option>
                <option value="guest">Invitado (Solo lectura)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- ACADÉMICO -->
        <div v-show="activeTab === 'academic'" class="card p-6 space-y-6 animate-fade-in">
          <div>
            <h2 class="text-lg font-bold mb-1">Reglas Académicas Globales</h2>
            <p class="text-sm text-[var(--color-text-muted)]">Valores por defecto para módulos y exámenes.</p>
          </div>
          <div class="space-y-6">
            <label class="flex items-center justify-between p-4 bg-[var(--color-app-bg)] rounded-lg border border-[var(--color-border)]">
              <div>
                <span class="text-sm font-bold block">Emisión automática de certificados</span>
                <span class="text-xs text-[var(--color-text-muted)]">Generar el PDF en cuanto el estudiante aprueba el 100% de un curso.</span>
              </div>
              <input type="checkbox" v-model="formData.auto_certificate" class="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
            </label>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="label">Puntaje global de aprobación (%)</label>
                <input type="number" v-model="formData.global_pass_score" min="1" max="100" class="input" />
              </div>
              <div>
                <label class="label">Límite de intentos global</label>
                <input type="number" v-model="formData.max_attempts" min="1" max="10" class="input" />
              </div>
            </div>
          </div>
        </div>

        <!-- BRANDING -->
        <div v-show="activeTab === 'branding'" class="card p-6 space-y-6 animate-fade-in">
          <div>
            <h2 class="text-lg font-bold mb-1">Branding e Identidad</h2>
            <p class="text-sm text-[var(--color-text-muted)]">Personalización visual del entorno de estudiante.</p>
          </div>
          <div class="grid md:grid-cols-2 gap-6">
            <div>
              <label class="label">Logo Principal</label>
              <div class="border-2 border-dashed border-[var(--color-border)] rounded-xl p-6 text-center text-sm text-[var(--color-text-muted)] hover:border-[var(--color-primary)] transition-colors cursor-pointer relative bg-[var(--color-app-bg)] group">
                <input type="file" accept="image/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                <div class="mx-auto w-10 h-10 rounded-full bg-[var(--color-primary-soft)] text-[var(--color-primary)] flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                  <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                </div>
                Arrastra o haz clic para subir
              </div>
            </div>
            <div>
              <label class="label">Color Primario (Énfasis)</label>
              <div class="flex items-center gap-3">
                <input type="color" v-model="formData.primary_color" class="w-12 h-12 rounded-lg border border-[var(--color-border)] cursor-pointer p-1 bg-white" />
                <input type="text" class="input flex-1 font-mono text-sm uppercase" v-model="formData.primary_color" />
              </div>
              <p class="text-xs text-[var(--color-text-muted)] mt-3">Este color se usará en botones, barras de progreso y elementos destacados de la plataforma.</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
