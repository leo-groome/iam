<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { z } from 'zod'
import { resetPasswordWithOtp } from '@/lib/auth-client'

const route = useRoute()

const email = ref(typeof route.query.email === 'string' ? route.query.email : '')
const code = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const isLoading = ref(false)
const error = ref('')
const success = ref(false)

const schema = z.object({
  email: z.string().email('Ingresa un correo valido'),
  code: z.string().trim().regex(/^\d{6}$/, 'Ingresa el codigo de 6 digitos'),
  password: z.string().min(8, 'La contrasena debe tener al menos 8 caracteres'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Las contrasenas no coinciden',
  path: ['confirmPassword'],
})

const canSubmit = computed(() => !isLoading.value && !success.value)

async function submit() {
  error.value = ''
  const parsed = schema.safeParse({
    email: email.value,
    code: code.value,
    password: password.value,
    confirmPassword: confirmPassword.value,
  })
  if (!parsed.success) {
    error.value = parsed.error.issues[0]?.message ?? 'Revisa los datos'
    return
  }

  isLoading.value = true
  try {
    await resetPasswordWithOtp(parsed.data.email, parsed.data.code, parsed.data.password)
    success.value = true
  } catch (err) {
    console.error('[auth] password reset failed:', err)
    error.value = 'No pudimos restablecer la contrasena. Revisa el codigo e intenta de nuevo.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main class="min-h-screen flex items-center justify-center px-4 py-10">
    <section class="w-full max-w-md">
      <div class="card p-6 sm:p-8">
        <h1 class="text-2xl font-bold tracking-tight">Nueva contrasena</h1>
        <p class="text-[var(--color-text-muted)] mt-2">
          Usa el codigo que recibiste por correo.
        </p>

        <div v-if="success" class="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
          Tu contrasena se actualizo correctamente.
          <RouterLink to="/login" class="font-semibold underline">
            Iniciar sesion
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

          <div>
            <label for="reset-code" class="label">Codigo</label>
            <input
              id="reset-code"
              v-model="code"
              type="text"
              inputmode="numeric"
              class="input tracking-[0.2em]"
              autocomplete="one-time-code"
              maxlength="6"
              placeholder="000000"
              required
            />
          </div>

          <div>
            <label for="reset-password" class="label">Nueva contrasena</label>
            <div class="relative">
              <input
                id="reset-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="input w-full pr-10"
                autocomplete="new-password"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 flex items-center pr-3 text-[var(--color-text-muted)]"
                tabindex="-1"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? 'Ocultar' : 'Ver' }}
              </button>
            </div>
          </div>

          <div>
            <label for="reset-confirm" class="label">Confirmar contrasena</label>
            <input
              id="reset-confirm"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              class="input"
              autocomplete="new-password"
              placeholder="••••••••"
              required
            />
          </div>

          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

          <button type="submit" class="btn btn-primary btn-block" :disabled="!canSubmit">
            {{ isLoading ? 'Guardando...' : 'Guardar nueva contrasena' }}
          </button>

          <RouterLink to="/recuperar-contrasena" class="btn btn-secondary btn-block text-center">
            Enviar otro codigo
          </RouterLink>
        </form>
      </div>
    </section>
  </main>
</template>
