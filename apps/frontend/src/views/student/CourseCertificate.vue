<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { coursesService } from '@/services/courses.service';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const slug = route.params.slug as string;

const curso = ref(null);
const loading = ref(true);

onMounted(async () => {
  try {
    curso.value = await coursesService.getBySlug(slug);
  } catch (err) {
    console.error(err);
    router.replace('/catalogo');
  } finally {
    loading.value = false;
  }
});

const studentName = authStore.user?.full_name || '';
const today = new Date().toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' });

const downloadPdf = () => {
  window.print();
};
</script>

<template>
  <div v-if="!loading && curso">
    <div class="text-center mb-8">
      <div class="text-6xl mb-3">🎓</div>
      <h1 class="text-4xl font-bold tracking-tight">¡Felicidades!</h1>
      <p class="text-[var(--color-text-muted)] mt-2 text-lg">Completaste el curso. Aquí tienes tu certificado.</p>
    </div>

    <!-- Contenedor principal del certificado -->
    <div class="relative w-full max-w-5xl bg-white shadow-xl overflow-hidden rounded-xl mb-8 border border-gray-100 print:shadow-none print:border-none print:m-0" style="aspect-ratio: 1.414 / 1;">
      
      <!-- Lado Izquierdo: FOTO con curva -->
      <div class="absolute inset-y-0 left-0 w-1/2 h-full z-10">
        <div class="w-full h-full curve-clip bg-[var(--color-primary-soft)] overflow-hidden relative">
          <img :src="curso.cover_key || curso.cover_url || '/Images/img-16.jpg'" 
               :alt="curso.title" 
               class="w-full h-full object-cover opacity-90">
          <div class="absolute inset-0 bg-[var(--color-primary)]/20 mix-blend-multiply"></div>
        </div>
      </div>

      <!-- Lado Derecho: CONTENIDO -->
      <div class="absolute inset-y-0 right-0 w-3/5 h-full z-0 flex flex-col justify-between p-6 sm:p-8 md:p-12 md:pl-24">
        
        <!-- Logo Superior Derecho -->
        <div class="self-end">
          <div class="w-16 h-16 md:w-24 md:h-24 rounded-full border-2 border-gray-200 bg-white flex items-center justify-center shadow-sm overflow-hidden">
            <img src="/MISIONERAS_LOGO.svg" class="w-10 h-10 md:w-16 md:h-16 object-contain" alt="Logo">
          </div>
        </div>

        <!-- Textos Centrales -->
        <div class="text-center mt-2 flex flex-col items-center justify-center flex-grow">
          <h2 class="text-[var(--color-primary)] font-bold tracking-[0.2em] uppercase text-xs md:text-sm mb-4 md:mb-8">Certificado de Finalización</h2>
          
          <p class="text-[var(--color-text-muted)] text-sm md:text-lg mb-1 md:mb-2">Se otorga con orgullo a</p>
          
          <!-- Línea 1 (Nombre) -->
          <div class="w-full flex justify-center">
            <h1 class="text-2xl sm:text-3xl md:text-5xl font-serif text-gray-900 border-b border-gray-300 pb-2 md:pb-3 px-4 md:px-8 inline-block" style="font-family: Georgia, serif;">{{ studentName }}</h1>
          </div>
          
          <p class="text-[var(--color-text-muted)] text-sm md:text-lg mt-4 md:mt-8 mb-1 md:mb-2">Por haber completado satisfactoriamente el curso</p>
          
          <!-- Línea 2 (Curso) -->
          <div class="w-full flex justify-center">
            <h3 class="text-lg sm:text-xl md:text-3xl font-bold text-gray-800 border-b border-gray-200 pb-1 md:pb-2 px-2 md:px-6 inline-block">{{ curso.title }}</h3>
          </div>
        </div>

        <!-- Firmas / Fechas (Líneas inferiores) -->
        <div class="flex justify-between items-end mt-4 md:mt-12 text-[var(--color-text-muted)] text-xs md:text-sm">
          <div class="text-center w-24 md:w-40">
            <div class="border-t border-gray-400 pt-1 md:pt-2 font-semibold text-gray-800">{{ today }}</div>
            <p>Fecha de emisión</p>
          </div>
          <div class="text-center w-24 md:w-40">
            <div class="border-t border-gray-400 pt-1 md:pt-2 font-semibold text-gray-800">#{{ curso.id.slice(0, 8).toUpperCase() }}</div>
            <p>ID del Certificado</p>
          </div>
        </div>

      </div>
    </div>

    <div class="space-y-3 print:hidden">
      <button @click="downloadPdf" class="btn btn-primary btn-block">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg>
        Descargar mi certificado
      </button>
      <router-link to="/catalogo" class="btn btn-secondary btn-block">Ver otros cursos</router-link>
    </div>
  </div>
</template>

<style scoped>
.curve-clip {
  clip-path: ellipse(75% 100% at 20% 50%);
}
</style>
