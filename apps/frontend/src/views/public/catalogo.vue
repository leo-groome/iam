<script setup lang="ts">
import { onMounted, computed, ref } from 'vue';
import CourseCard from "@/components/ui/CourseCard.vue";
import SkeletonCard from "@/components/ui/SkeletonCard.vue";
import GreetingHeader from "@/components/ui/GreetingHeader.vue";
import { useAuthStore } from '@/stores/auth';
import { useCatalogStore } from '@/stores/catalog';

const authStore = useAuthStore();
const catalogStore = useCatalogStore();

// Show cached data instantly; loading only true when there's no cache yet
const courses = computed(() => catalogStore.courses);
const loading = computed(() => !catalogStore.courses.length && catalogStore.loading);

onMounted(() => {
  // Always refetch in background to stay fresh.
  // If cache exists, content shows immediately while this runs silently.
  catalogStore.refetch();
});

const enProgreso = computed(() => catalogStore.courses.filter((c: any) => c.progress_pct > 0 && c.progress_pct < 100));
const nuevos = computed(() => catalogStore.courses.filter((c: any) => !c.progress_pct || c.progress_pct === 0));
const completados = computed(() => catalogStore.courses.filter((c: any) => c.progress_pct === 100));

const IMG = "/Images";

const allPhotos: string[] = [
  `${IMG}/img-01.png`, `${IMG}/img-02.png`, `${IMG}/img-03.jpg`, `${IMG}/img-04.png`,
  `${IMG}/img-05.jpg`, `${IMG}/img-06.jpg`, `${IMG}/img-07.jpg`, `${IMG}/img-08.jpg`,
  `${IMG}/img-09.jpg`, `${IMG}/img-10.jpg`, `${IMG}/img-11.jpg`, `${IMG}/img-13.png`,
  `${IMG}/img-14.jpg`, `${IMG}/img-16.jpg`, `${IMG}/img-18.png`, `${IMG}/img-19.jpg`,
  `${IMG}/img-20.jpg`, `${IMG}/img-21.jpg`, `${IMG}/img-22.jpg`, `${IMG}/img-23.jpg`,
  `${IMG}/img-24.jpg`, `${IMG}/img-25.jpg`, `${IMG}/img-26.jpg`, `${IMG}/img-27.jpg`,
  `${IMG}/img-28.jpg`, `${IMG}/img-29.jpg`, `${IMG}/img-30.jpg`, `${IMG}/img-31.jpg`,
  `${IMG}/img-32.jpg`, `${IMG}/img-33.jpg`, `${IMG}/img-34.jpg`, `${IMG}/img-35.jpg`,
  `${IMG}/img-36.jpg`, `${IMG}/img-37.jpg`, `${IMG}/img-38.jpg`, `${IMG}/img-39.jpg`,
  `${IMG}/img-40.jpg`, `${IMG}/img-41.jpg`, `${IMG}/img-42.jpg`, `${IMG}/img-43.jpg`,
  `${IMG}/img-44.jpg`, `${IMG}/img-45.jpg`, `${IMG}/img-46.jpg`, `${IMG}/img-47.jpg`,
  `${IMG}/img-48.jpg`, `${IMG}/img-49.jpg`, `${IMG}/img-50.jpg`,
];

function seededShuffle<T>(arr: T[], seed: number): T[] {
  const a = [...arr];
  let s = seed;
  for (let i = a.length - 1; i > 0; i--) {
    s = (s * 9301 + 49297) % 233280;
    const j = Math.floor((s / 233280) * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const photos = ref(seededShuffle(allPhotos, 42).slice(0, 36));

const rots = [-4, 3, -2, 4, 2, -3, 5, -5, 3, -2, 4, -4];
const yOffsets = [0, 4, -4, 6, -6, 2, -2, 5, -5, 0, 3, -3];
</script>

<template>
  <div class="relative min-h-screen -mb-32 pb-48">
    <div
      aria-hidden="true"
      class="absolute inset-y-0 pointer-events-none overflow-hidden"
      style="left: 50%; transform: translateX(-50%); width: 100vw; z-index: 0;"
    >
      <div
        class="relative w-full h-full opacity-75 grid gap-8 sm:gap-12 p-6 sm:p-10"
        style="grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));"
      >
        <div
          v-for="(src, i) in photos"
          :key="src"
          class="rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/50 bg-[var(--color-primary-soft)]"
          :style="`aspect-ratio: 4/5; transform: rotate(${rots[i % rots.length]}deg) translateY(${yOffsets[i % yOffsets.length]}px);`"
        >
          <img
            :src="src"
            alt=""
            class="w-full h-full object-cover"
            loading="lazy"
            onerror="this.style.display='none'"
          />
        </div>
      </div>
      <div class="absolute inset-0 bg-gradient-to-b from-[var(--color-app-bg)]/55 via-[var(--color-app-bg)]/40 to-[var(--color-app-bg)]/75"></div>
    </div>

    <div class="relative max-w-4xl mx-auto px-4 sm:px-6 pt-10" style="z-index: 1;">
      <header class="card px-6 py-5 sm:px-8 sm:py-6 mb-6 rounded-3xl">
        <div class="grid md:grid-cols-[1fr_auto] gap-6 md:gap-10 items-center">
          <div>
            <h1 class="text-4xl sm:text-5xl font-bold tracking-tight">Cursos</h1>
            <GreetingHeader :name="authStore.user?.full_name?.split(' ')[0] || 'Estudiante'" />
          </div>

          <figure class="relative md:max-w-sm md:border-l md:border-[var(--color-border)] md:pl-8 border-t md:border-t-0 border-[var(--color-border)] pt-5 md:pt-0">
            <span class="absolute -top-3 md:-top-5 left-0 md:left-6 text-[var(--color-primary)] text-5xl leading-none select-none font-serif">“</span>
            <blockquote class="text-[var(--color-text)] italic leading-relaxed text-sm sm:text-base">
              ¿Puede una madre olvidar a su niño de pecho? Aunque ella se olvidara, yo no te olvidaría. Te llevo grabado en las palmas de mis manos.
            </blockquote>
            <figcaption class="text-xs text-[var(--color-primary)] mt-2 font-semibold tracking-wider uppercase">
              Isaías 49:15-16
            </figcaption>
          </figure>
        </div>
      </header>

      <transition name="fade" mode="out-in">
        <div v-if="loading" class="space-y-10">
          <section>
            <h2 class="text-lg font-semibold mb-3">Cursos disponibles</h2>
            <div class="grid gap-4">
              <SkeletonCard v-for="i in 3" :key="i" :hasImage="true" :hasIcon="false" :hasSubtitle="true" :hasFooter="true" class="h-40" />
            </div>
          </section>
        </div>

        <div v-else class="space-y-10">
          <template v-if="courses.length > 0">
            <section v-if="enProgreso.length > 0">
              <h2 class="text-lg font-semibold mb-3">Continuar donde lo dejé</h2>
              <div class="grid gap-4">
                <CourseCard v-for="c in enProgreso" :key="c.id" :slug="c.slug" :title="c.title" :description="c.short_desc" :progress="c.progress_pct" :cover="c.cover_key || '/placeholder.jpg'" :href="`/curso/${c.slug}?auto_resume=1`" />
              </div>
            </section>

            <section v-if="nuevos.length > 0">
              <h2 class="text-lg font-semibold mb-3">Cursos disponibles</h2>
              <div class="grid gap-4">
                <CourseCard v-for="c in nuevos" :key="c.id" :slug="c.slug" :title="c.title" :description="c.short_desc" :cover="c.cover_key || '/placeholder.jpg'" />
              </div>
            </section>

            <section v-if="completados.length > 0">
              <h2 class="text-lg font-semibold mb-3">Ya completados</h2>
              <div class="grid gap-4">
                <CourseCard v-for="c in completados" :key="c.id" :slug="c.slug" :title="c.title" :description="c.short_desc" :progress="100" :cover="c.cover_key || '/placeholder.jpg'" cta="Ver certificado" :href="`/curso/${c.slug}/certificado`" />
              </div>
            </section>
          </template>
          <template v-else>
             <div class="card p-10 text-center rounded-3xl mt-12 bg-white/80 backdrop-blur border border-[var(--color-border)] shadow-xl relative z-10">
               <svg class="w-16 h-16 mx-auto text-[var(--color-primary)] mb-4 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>
               <h2 class="text-2xl font-bold mb-2">Cursos disponibles próximamente</h2>
               <p class="text-[var(--color-text-muted)] max-w-md mx-auto">Estamos preparando nuevo contenido para ti. Vuelve pronto para descubrir nuestros nuevos cursos.</p>
             </div>
          </template>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
:deep(body) { background: transparent !important; }
</style>
