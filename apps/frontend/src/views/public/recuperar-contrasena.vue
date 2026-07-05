<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { z } from 'zod'
import { requestPasswordResetOtp } from '@/lib/auth-client'

const email = ref('')
const isLoading = ref(false)
const error = ref('')
const sent = ref(false)

const schema = z.object({
  email: z.string().email('Ingresa un correo valido'),
})

async function submit() {
  error.value = ''
  const parsed = schema.safeParse({ email: email.value })
  if (!parsed.success) {
    error.value = parsed.error.issues[0]?.message ?? 'Correo invalido'
    return
  }

  isLoading.value = true
  try {
    await requestPasswordResetOtp(parsed.data.email)
    sent.value = true
  } catch (err) {
    console.error('[auth] password reset request failed:', err)
    error.value = 'No pudimos enviar el codigo. Intenta de nuevo.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main class="min-h-screen flex items-center justify-center px-4 py-10">
    <section class="w-full max-w-md">
      <RouterLink to="/login" class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
        ← Volver a iniciar sesion
      </RouterLink>

      <div class="card p-6 sm:p-8 mt-4">
        <h1 class="text-2xl font-bold tracking-tight">Recuperar contrasena</h1>
        <p class="text-[var(--color-text-muted)] mt-2">
          Te enviaremos un codigo para crear una nueva contrasena.
        </p>

        <div v-if="sent" class="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          Si existe una cuenta con ese correo, enviamos un codigo de recuperacion.
          <RouterLink
            :to="{ path: '/restablecer-contrasena', query: { email } }"
            class="font-semibold underline"
          >
            Continuar
          </RouterLink>
        </div>

        <form v-else class="mt-6 space-y-4" novalidate @submit.prevent="submit">
          <div>
            <label for="reset-email" class="label">Correo</label>
            <input
              id="reset-email"
              v-model="email"
              type="email"
              class="input"
              autocomplete="email"
              placeholder="tu@correo.com"
              required
            />
          </div>

          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

          <button type="submit" class="btn btn-primary btn-block" :disabled="isLoading">
            {{ isLoading ? 'Enviando...' : 'Enviar codigo' }}
          </button>
        </form>
      </div>
    </section>
  </main>
</template>
