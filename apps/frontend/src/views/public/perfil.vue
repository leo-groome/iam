<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { coursesService } from '@/services/courses.service';

const authStore = useAuthStore();
const courses = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const data = await coursesService.getAll();
    courses.value = data.items || [];
  } catch (err) {
    console.error('Error loading courses:', err);
  } finally {
    loading.value = false;
  }
});

const completados = computed(() => courses.value.filter(c => c.progress_pct === 100));

const user = computed(() => authStore.user || {});
const initials = computed(() => {
  const parts = user.value?.full_name?.split(' ') || [];
  return (parts[0]?.[0] || '') + (parts[1]?.[0] || '');
});

const age = computed(() => {
  if (!user.value?.birth_date) return null;
  const today = new Date();
  const birthDate = new Date(user.value.birth_date);
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
});
</script>

<template>
  <h1 class="text-3xl font-bold mb-6">Mi perfil</h1>

  <div class="card p-6 mb-6 flex items-center gap-4">
    <img :src="`https://api.dicebear.com/9.x/bottts/svg?seed=${encodeURIComponent(user.full_name || user.email || 'avatar')}`" alt="Avatar" class="w-16 h-16 rounded-full bg-blue-100 shrink-0" />
    <div>
      <p class="font-bold text-lg">{{ user.full_name }}</p>
      <p class="text-[var(--color-text-muted)] text-sm">{{ user.email }}</p>
      <p v-if="age" class="text-[var(--color-text-muted)] text-xs mt-1">Edad: {{ age }} años</p>
    </div>
  </div>

  <h2 class="text-lg font-semibold mb-3">Mis certificados</h2>
  <div v-if="!loading && completados.length === 0" class="card p-8 text-center text-[var(--color-text-muted)]">
    Aún no tienes certificados. ¡Completa tu primer curso!
  </div>
  <div v-else-if="!loading" class="space-y-3 mb-8">
    <router-link v-for="c in completados" :key="c.id" :to="`/curso/${c.slug}/certificado`" class="card p-4 flex items-center gap-3 hover:border-[var(--color-primary)] transition">
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
