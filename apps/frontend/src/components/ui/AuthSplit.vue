<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{ initialMode?: 'login' | 'register' }>();
const mode = ref<'login' | 'register'>(props.initialMode ?? 'login');

function toggle() {
  mode.value = mode.value === 'login' ? 'register' : 'login';
}
</script>

<template>
  <div class="relative min-h-screen lg:overflow-hidden">

    <aside
      class="lg:absolute lg:inset-y-0 lg:left-0 lg:w-1/2 transition-transform duration-[700ms] ease-[cubic-bezier(0.65,0,0.35,1)] hidden lg:flex overflow-hidden"
      :class="mode === 'register' ? 'lg:translate-x-full' : 'lg:translate-x-0'"
    >
      <img src="/Images/img-16.jpg" alt="" class="absolute inset-0 w-full h-full object-cover" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-black/20"></div>

      <div class="relative z-10 flex flex-col justify-between p-12 xl:p-16 text-white w-full">
        <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-20 w-auto brightness-0 invert" />

        <div class="max-w-md">
          <p class="text-sm uppercase tracking-[0.2em] text-white/70 mb-3 font-medium">Plataforma de formación</p>
          <h2 class="text-4xl xl:text-5xl font-bold leading-tight tracking-tight">
            Aprender es <br/><em class="text-white/85 not-italic">acompañar la vida.</em>
          </h2>
          <p class="mt-5 text-white/80 leading-relaxed">
            Una plataforma diseñada para crecer en humanidad. Avanza a tu ritmo, con cursos breves y guiados.
          </p>
        </div>

        <figure class="border-l-2 border-white/40 pl-4 max-w-md">
          <blockquote class="italic text-white/95 leading-relaxed">
            "¿Puede una madre olvidar a su niño de pecho? Aunque ella se olvidara, yo no te olvidaría."
          </blockquote>
          <figcaption class="text-xs text-white/70 mt-2 font-semibold tracking-wider uppercase">
            Isaías 49:15
          </figcaption>
        </figure>
      </div>
    </aside>

    <main
      class="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2 transition-transform duration-[700ms] ease-[cubic-bezier(0.65,0,0.35,1)] flex items-center justify-center px-4 py-10 sm:px-6 lg:px-12"
      :class="mode === 'register' ? 'lg:-translate-x-full' : 'lg:translate-x-0'"
    >
      <div class="w-full max-w-md">

        <div class="text-center lg:hidden mb-8">
          <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-16 w-auto mx-auto" />
        </div>

        <Transition mode="out-in" enter-active-class="transition duration-300 ease-out" leave-active-class="transition duration-200 ease-in" enter-from-class="opacity-0 translate-y-2" leave-to-class="opacity-0 -translate-y-2">
          <div v-if="mode === 'login'" key="login">
            <div class="hidden lg:block mb-8">
              <p class="text-sm text-[var(--color-primary)] font-semibold uppercase tracking-wider">Iniciar sesión</p>
              <h1 class="text-3xl font-bold mt-1">Bienvenido de vuelta</h1>
              <p class="text-[var(--color-text-muted)] mt-2">Continúa tu formación donde la dejaste.</p>
            </div>

            <div class="lg:hidden text-center mb-6">
              <h1 class="text-2xl font-bold">Bienvenido</h1>
              <p class="text-[var(--color-text-muted)] mt-1">Tu formación, paso a paso.</p>
            </div>

            <button class="btn btn-secondary btn-block mb-3">
              <svg width="20" height="20" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8a12 12 0 010-24c3 0 5.8 1.1 7.9 3l5.7-5.7A20 20 0 1024 44c11 0 20-9 20-20 0-1.2-.1-2.3-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3 0 5.8 1.1 7.9 3l5.7-5.7A20 20 0 006.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2c-2 1.4-4.4 2.2-7.2 2.2-5.2 0-9.6-3.3-11.3-8L6.2 33A20 20 0 0024 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.6L37.4 39c4.1-3.8 6.6-9.4 6.6-15 0-1.2-.1-2.3-.4-3.5z"/></svg>
              Entrar con Google
            </button>

            <div class="relative my-4">
              <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-[var(--color-border)]"></div></div>
              <div class="relative flex justify-center"><span class="bg-[var(--color-app-bg)] px-2 text-xs text-[var(--color-text-muted)]">o entra con tu correo</span></div>
            </div>

            <form action="/catalogo" class="space-y-3">
              <div>
                <label class="label" for="login-email">Correo</label>
                <input id="login-email" type="email" class="input" placeholder="tu@correo.com" />
              </div>
              <div>
                <label class="label" for="login-password">Contraseña</label>
                <input id="login-password" type="password" class="input" placeholder="••••••••" />
              </div>
              <button type="submit" class="btn btn-primary btn-block">Iniciar sesión</button>
            </form>

            <p class="text-center text-sm text-[var(--color-text-muted)] mt-6">
              ¿Primera vez?
              <button type="button" @click="toggle" class="text-[var(--color-primary)] font-semibold hover:underline">
                Crear cuenta
              </button>
            </p>
          </div>

          <div v-else key="register">
            <div class="hidden lg:block mb-8">
              <p class="text-sm text-[var(--color-primary)] font-semibold uppercase tracking-wider">Crear cuenta</p>
              <h1 class="text-3xl font-bold mt-1">Empieza tu camino</h1>
              <p class="text-[var(--color-text-muted)] mt-2">Es gratis y solo te toma un minuto.</p>
            </div>

            <div class="lg:hidden text-center mb-6">
              <h1 class="text-2xl font-bold">Crea tu cuenta</h1>
              <p class="text-[var(--color-text-muted)] mt-1">Es gratis y rápido.</p>
            </div>

            <form action="/catalogo" class="space-y-3">
              <div>
                <label class="label" for="reg-nombre">Nombre completo</label>
                <input id="reg-nombre" type="text" class="input" placeholder="Tu nombre" required minlength="3" maxlength="80" />
              </div>
              <div>
                <label class="label" for="reg-email">Correo</label>
                <input id="reg-email" type="email" class="input" placeholder="tu@correo.com" required maxlength="120" />
              </div>
              <div>
                <label class="label" for="reg-password">Contraseña</label>
                <input id="reg-password" type="password" class="input" placeholder="Mínimo 8 caracteres" required minlength="8" />
              </div>
              <div>
                <label class="label" for="reg-fecha">Fecha de nacimiento</label>
                <input id="reg-fecha" type="date" class="input" required />
              </div>
              <label class="flex items-start gap-2 text-sm">
                <input type="checkbox" required class="mt-1" />
                <span>Acepto los <a href="/terminos" target="_blank" class="text-[var(--color-primary)] underline">Términos</a> y el <a href="/privacidad" target="_blank" class="text-[var(--color-primary)] underline">Aviso de Privacidad</a>.</span>
              </label>
              <button type="submit" class="btn btn-primary btn-block">Crear mi cuenta</button>
            </form>

            <p class="text-center text-sm text-[var(--color-text-muted)] mt-6">
              ¿Ya tienes cuenta?
              <button type="button" @click="toggle" class="text-[var(--color-primary)] font-semibold hover:underline">
                Iniciar sesión
              </button>
            </p>
          </div>
        </Transition>
      </div>
    </main>
  </div>
</template>
