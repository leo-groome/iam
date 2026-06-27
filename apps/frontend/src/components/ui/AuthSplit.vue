<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import {
  assertAuthConfigured,
  authClient,
  hasAuthConfig,
  isMockAuthAllowed,
  refreshAuthTokenCookie,
  sendEmailVerificationOtp,
  setMockAuthToken,
} from '@/lib/auth-client'
import { ApiError, apiGet } from '@/lib/api'
import { useAuthStore, type OnboardingPayload } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

// ---------------------------------------------------------------------------
// Onboarding cache — read once. Used to prefill the name field and to bundle
// the demographic answers into the /auth/sync call at signup.
// ---------------------------------------------------------------------------
const ONBOARDING_KEYS = ['edad', 'sexo', 'diocesis', 'ciudad', 'parroquia', 'entorno', 'pastoral'] as const

function readOnboardingCache(): Record<string, string> | null {
  try {
    const raw = sessionStorage.getItem('onboardingData')
    return raw ? (JSON.parse(raw) as Record<string, string>) : null
  } catch {
    return null
  }
}

const onboardingData = readOnboardingCache()

function buildOnboardingPayload(): OnboardingPayload | undefined {
  const d = onboardingData
  if (!d) return undefined
  // `nombre` is intentionally dropped (it maps to full_name). Bail if any
  // required demographic answer is missing so the backend isn't sent a partial.
  if (!ONBOARDING_KEYS.every((k) => typeof d[k] === 'string' && d[k])) return undefined
  return {
    edad: d.edad,
    sexo: d.sexo,
    diocesis: d.diocesis,
    ciudad: d.ciudad,
    parroquia: d.parroquia,
    entorno: d.entorno,
    pastoral: d.pastoral,
  }
}

// After a successful signup, route new registrants (those who came through the
// onboarding flow) into the general diagnostic when one is configured; otherwise
// fall back to the catalog. The cache is cleared by the store after sync.
async function resolvePostSignupRedirect(): Promise<string> {
  if (!onboardingData) return nextRedirect
  try {
    const res = (await apiGet('/api/v1/diagnostic/active')) as { active: unknown }
    if (res && res.active) return '/diagnostico'
  } catch {
    // No diagnostic configured / network error — skip straight to the catalog.
  }
  return nextRedirect
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
const props = defineProps<{
  initialMode?: 'login' | 'register'
  /** Redirect destination after a successful auth flow. */
  nextUrl?: string
}>()

// ---------------------------------------------------------------------------
// UI state
// ---------------------------------------------------------------------------
const mode = ref<'login' | 'register'>(props.initialMode ?? 'login')
const isLoading = ref(false)
const isReady = ref(false)
const isCompletingOAuthProfile = ref(false)
const toast = ref<{ type: 'error' | 'success'; message: string } | null>(null)

function toggle() {
  const target = mode.value === 'login' ? '/signup' : '/login'
  toast.value = null
  router.push({ path: target, query: router.currentRoute.value.query })
}

function showToast(type: 'error' | 'success', message: string) {
  toast.value = { type, message }
}

function clearToast() {
  toast.value = null
}

// ---------------------------------------------------------------------------
// Max birth date = today minus 13 years (UX guard; backend is the authority)
// ---------------------------------------------------------------------------
const maxDob = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 13)
  return d.toISOString().split('T')[0]
})

function getBirthDateFromAgeRange(edad: string): string {
  const today = new Date()
  let age = 18 // fallback
  if (edad === '<18') {
    age = 15
  } else if (edad === '18-25') {
    age = 21
  } else if (edad === '26-35') {
    age = 30
  } else if (edad === '36-50') {
    age = 43
  } else if (edad === '>50') {
    age = 60
  }
  const birthYear = today.getFullYear() - age
  return `${birthYear}-01-01`
}

// ---------------------------------------------------------------------------
// Read ?next= from query string for post-auth redirect
// ---------------------------------------------------------------------------
let nextRedirect = props.nextUrl ?? '/catalogo'
onMounted(() => {
  if (typeof window !== 'undefined') {
    const params = new URLSearchParams(window.location.search)
    const next = params.get('next')
    if (next && next.startsWith('/')) nextRedirect = next
  }
  isReady.value = true

  if (mode.value === 'register' && !onboardingData) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('hasCompletedOnboarding')
      router.push({ path: '/onboarding', query: router.currentRoute.value.query })
    }
    return
  }

  // Prefill name and birth date from onboarding data
  if (onboardingData) {
    if (onboardingData.nombre && !regFullName.value) {
      regFullName.value = onboardingData.nombre
    }
    if (onboardingData.edad && !regBirthDate.value) {
      regBirthDate.value = getBirthDateFromAgeRange(onboardingData.edad)
    }
  }

  // Only enter "complete your profile" mode when the user actually returned
  // from an OAuth callback (?oauth=1). Otherwise a leftover Neon session would
  // hijack the regular signup form.
  const cameFromOAuth = new URLSearchParams(window.location.search).get('oauth') === '1'
  if (mode.value === 'register' && cameFromOAuth && hasAuthConfig() && !isMockAuthAllowed()) {
    authClient.getSession().then(({ data }) => {
      isCompletingOAuthProfile.value = Boolean(data?.session && data?.user)
    }).catch(() => {
      isCompletingOAuthProfile.value = false
    })
  }
})

// ---------------------------------------------------------------------------
// Zod schemas — client-side validation (UX layer, not security)
// ---------------------------------------------------------------------------
const loginSchema = z.object({
  email: z.string().email('Correo inválido'),
  password: z.string().min(1, 'La contraseña es requerida'),
})

const registerSchema = z.object({
  fullName: z
    .string()
    .min(3, 'El nombre debe tener al menos 3 caracteres')
    .max(80, 'Nombre demasiado largo'),
  email: z.string().email('Correo inválido').max(120, 'Correo demasiado largo'),
  password: z.string().min(8, 'La contraseña debe tener al menos 8 caracteres'),
  birthDate: z
    .string()
    .min(1, 'La fecha de nacimiento es requerida')
    .refine((d) => {
      const dob = new Date(d)
      const minAge = new Date()
      minAge.setFullYear(minAge.getFullYear() - 13)
      return dob <= minAge
    }, 'Debes ser mayor de 13 años para registrarte'),
  terms: z.literal(true, { errorMap: () => ({ message: 'Debes aceptar los términos' }) }),
})

// ---------------------------------------------------------------------------
// Login — form refs
// ---------------------------------------------------------------------------
const loginEmail = ref('')
const loginPassword = ref('')
const loginErrors = ref<Record<string, string>>({})

async function handleLogin() {
  clearToast()
  loginErrors.value = {}

  const parsed = loginSchema.safeParse({ email: loginEmail.value, password: loginPassword.value })
  if (!parsed.success) {
    parsed.error.issues.forEach((i) => {
      loginErrors.value[i.path[0] as string] = i.message
    })
    return
  }

  isLoading.value = true
  try {
    if (isMockAuthAllowed()) {
      setMockAuthToken(parsed.data.email, 'Student User')
      await authStore.init()
      window.location.href = nextRedirect
      return
    }

    await authStore.login(parsed.data.email, parsed.data.password)
    window.location.href = nextRedirect
  } catch (err: unknown) {
    showToast('error', classifyAuthError(err))
  } finally {
    isLoading.value = false
  }
}

async function handleGoogleLogin() {
  clearToast()
  isLoading.value = true
  try {
    assertAuthConfigured()
    // OAuth redirects externally; on return the router's beforeEach will call init()
    // which hydrates the store. callbackURL lands on a protected page, triggering fetchMe.
    await authClient.signIn.social({
      provider: 'google',
      callbackURL: window.location.origin + nextRedirect,
      newUserCallbackURL: window.location.origin + '/signup?oauth=1',
      errorCallbackURL: window.location.origin + '/login',
    })
  } catch (err: unknown) {
    showToast('error', 'No se pudo iniciar el flujo con Google. Intenta de nuevo.')
    isLoading.value = false
  }
}

// ---------------------------------------------------------------------------
// Register — form refs
// ---------------------------------------------------------------------------
const regFullName = ref('')
const regEmail = ref('')
const regPassword = ref('')
const regBirthDate = ref('')
const regTerms = ref(false)
const verificationCode = ref('')
const regErrors = ref<Record<string, string>>({})
const pendingRegistration = ref<{
  fullName: string
  email: string
  password: string
  birthDate: string
} | null>(null)

const verificationSchema = z.object({
  code: z.string().trim().regex(/^\d{6}$/, 'Ingresa el código de 6 dígitos'),
})

async function handleVerifyRegistration() {
  clearToast()
  regErrors.value = {}

  const pending = pendingRegistration.value
  if (!pending) return

  const parsed = verificationSchema.safeParse({ code: verificationCode.value })
  if (!parsed.success) {
    regErrors.value.verificationCode = parsed.error.issues[0]?.message ?? 'Código inválido'
    return
  }

  isLoading.value = true
  try {
    await authStore.verifyOtp(
      pending.email,
      parsed.data.code,
      pending.fullName,
      pending.birthDate,
      buildOnboardingPayload(),
    )
    // fetchMe was already called inside verifyOtp — user is populated
    window.location.href = await resolvePostSignupRedirect()
  } catch (err: unknown) {
    console.error('[auth] verification failed:', err)
    if (err instanceof ApiError && err.status === 401) {
      showToast('error', 'Neon verificó el código, pero el backend no pudo validar el JWT. Revisa Auth URL/JWKS.')
    } else {
      showToast('error', classifyAuthError(err))
    }
  } finally {
    isLoading.value = false
  }
}

async function resendVerificationCode() {
  const pending = pendingRegistration.value
  if (!pending) return

  clearToast()
  isLoading.value = true
  try {
    assertAuthConfigured()
    await sendEmailVerificationOtp(pending.email)
    showToast('success', 'Te enviamos un nuevo código.')
  } catch (err: unknown) {
    console.error('[auth] resend verification failed:', err)
    showToast('error', 'No pudimos reenviar el código. Intenta de nuevo.')
  } finally {
    isLoading.value = false
  }
}

async function handleRegister() {
  if (pendingRegistration.value) {
    await handleVerifyRegistration()
    return
  }

  clearToast()
  regErrors.value = {}

  const parsed = registerSchema.safeParse({
    fullName: regFullName.value,
    email: isCompletingOAuthProfile.value ? 'oauth@example.com' : regEmail.value,
    password: isCompletingOAuthProfile.value ? 'oauth-placeholder-password' : regPassword.value,
    birthDate: regBirthDate.value,
    terms: regTerms.value || undefined,
  })

  if (!parsed.success) {
    parsed.error.issues.forEach((i) => {
      regErrors.value[i.path[0] as string] = i.message
    })
    return
  }

  isLoading.value = true
  try {
    if (isCompletingOAuthProfile.value) {
      // OAuth profile completion: session cookie already set by OAuth provider,
      // just get the JWT, sync the profile, then hydrate user.
      const { apiPost: syncPost } = await import('@/lib/api')
      await refreshAuthTokenCookie()
      const payload = buildOnboardingPayload()
      await syncPost('/api/v1/auth/sync', {
        body: { full_name: parsed.data.fullName, birth_date: parsed.data.birthDate, onboarding: payload ?? null },
      })
      if (payload) sessionStorage.removeItem('onboardingData')
      await authStore.fetchMe()
      window.location.href = await resolvePostSignupRedirect()
      return
    } else if (isMockAuthAllowed()) {
      setMockAuthToken(parsed.data.email, parsed.data.fullName)
      // Redirect — router beforeEach will call init() which picks up the new mock token
      window.location.href = nextRedirect
      return
    } else {
      const result = await authStore.register(
        parsed.data.email,
        parsed.data.password,
        parsed.data.fullName,
      )
      if (result.status === 'pending_verification') {
        pendingRegistration.value = {
          fullName: parsed.data.fullName,
          email: parsed.data.email,
          password: parsed.data.password,
          birthDate: parsed.data.birthDate,
        }
        verificationCode.value = ''
        showToast('success', 'Te enviamos un código de verificación a tu correo.')
        return
      }
    }
  } catch (err: unknown) {
    console.error('[auth] register failed:', err)
    if (err instanceof ApiError) {
      if (err.status === 403) {
        showToast('error', 'Debes ser mayor de 13 años para registrarte en esta plataforma.')
      } else if (err.status === 401) {
        showToast('error', 'No pudimos validar tu sesión de Neon Auth. Revisa la configuración de Auth URL/JWKS.')
      } else if (err.status === 409) {
        showToast('error', 'Ya existe una cuenta con ese correo. Inicia sesión.')
      } else {
        showToast('error', 'Ocurrió un error al crear tu cuenta. Intenta de nuevo.')
      }
    } else {
      showToast('error', classifyAuthError(err))
    }
  } finally {
    isLoading.value = false
  }
}

// ---------------------------------------------------------------------------
// Maps SDK/network errors to safe user-facing strings.
// NEVER pass raw err.message to the UI — may contain internal detail.
// ---------------------------------------------------------------------------
function classifyAuthError(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message.toLowerCase()
    if (msg.includes('otp') || msg.includes('code')) {
      return 'El código no es válido o expiró. Revisa tu correo e intenta de nuevo.'
    }
    if (msg.includes('verify') || msg.includes('verification') || msg.includes('verified')) {
      return 'Revisa tu correo y verifica tu cuenta antes de continuar.'
    }
    if (msg.includes('invalid') || msg.includes('incorrect') || msg.includes('wrong')) {
      return 'Correo o contraseña incorrectos.'
    }
    if (msg.includes('email') && msg.includes('exist')) {
      return 'Ya existe una cuenta con ese correo.'
    }
    if (msg.includes('network') || msg.includes('fetch')) {
      return 'Error de conexión. Verifica tu internet e intenta de nuevo.'
    }
  }
  return 'Algo salió mal. Intenta de nuevo en unos momentos.'
}
</script>

<template>
  <div class="relative min-h-screen lg:overflow-hidden" :data-auth-ready="isReady ? 'true' : 'false'">

    <!-- Decorative aside (desktop only) -->
    <aside
      class="lg:absolute lg:inset-y-0 lg:left-0 lg:w-1/2 transition-transform duration-[700ms] ease-[cubic-bezier(0.65,0,0.35,1)] hidden lg:flex overflow-hidden"
      :class="mode === 'register' ? 'lg:translate-x-full' : 'lg:translate-x-0'"
    >
      <img :src="'/Images/img-16.jpg'" alt="" class="absolute inset-0 w-full h-full object-cover" />
      <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-black/20"></div>

      <div class="relative z-10 flex flex-col justify-between p-12 xl:p-16 text-white w-full">
        <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-20 w-auto brightness-0 invert" />

        <div class="max-w-md">
          <p class="text-sm uppercase tracking-[0.2em] text-white/70 mb-3 font-medium">Plataforma de formación</p>
          <h2 class="text-4xl xl:text-5xl font-bold leading-tight tracking-tight">
            Aprender es <br /><em class="text-white/85 not-italic">acompañar la vida.</em>
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

    <!-- Main form panel -->
    <main
      class="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2 transition-transform duration-[700ms] ease-[cubic-bezier(0.65,0,0.35,1)] flex items-center justify-center px-4 py-10 sm:px-6 lg:px-12"
      :class="mode === 'register' ? 'lg:-translate-x-full' : 'lg:translate-x-0'"
    >
      <div class="w-full max-w-md">

        <!-- Mobile logo -->
        <div class="text-center lg:hidden mb-8">
          <img src="/MISIONERAS_LOGO.svg" alt="Misioneras" class="h-16 w-auto mx-auto" />
        </div>

        <!-- Toast notification -->
        <Transition
          enter-active-class="transition duration-200 ease-out"
          leave-active-class="transition duration-150 ease-in"
          enter-from-class="opacity-0 -translate-y-1"
          leave-to-class="opacity-0 -translate-y-1"
        >
          <div
            v-if="toast"
            class="mb-4 rounded-lg px-4 py-3 text-sm font-medium"
            :class="toast.type === 'error'
              ? 'bg-red-50 text-red-700 border border-red-200'
              : 'bg-green-50 text-green-700 border border-green-200'"
            role="alert"
            aria-live="polite"
          >
            {{ toast.message }}
          </div>
        </Transition>

        <Transition
          mode="out-in"
          enter-active-class="transition duration-300 ease-out"
          leave-active-class="transition duration-200 ease-in"
          enter-from-class="opacity-0 translate-y-2"
          leave-to-class="opacity-0 -translate-y-2"
        >
          <!-- ============================================================ -->
          <!-- LOGIN                                                         -->
          <!-- ============================================================ -->
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

            <!-- Google OAuth -->
            <button
              type="button"
              class="btn btn-secondary btn-block mb-3"
              :disabled="isLoading"
              @click="handleGoogleLogin"
            >
              <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
                <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8a12 12 0 010-24c3 0 5.8 1.1 7.9 3l5.7-5.7A20 20 0 1024 44c11 0 20-9 20-20 0-1.2-.1-2.3-.4-3.5z"/>
                <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3 0 5.8 1.1 7.9 3l5.7-5.7A20 20 0 006.3 14.7z"/>
                <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2c-2 1.4-4.4 2.2-7.2 2.2-5.2 0-9.6-3.3-11.3-8L6.2 33A20 20 0 0024 44z"/>
                <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.6L37.4 39c4.1-3.8 6.6-9.4 6.6-15 0-1.2-.1-2.3-.4-3.5z"/>
              </svg>
              Entrar con Google
            </button>

            <div class="relative my-4">
              <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-[var(--color-border)]"></div></div>
              <div class="relative flex justify-center"><span class="bg-[var(--color-app-bg)] px-2 text-xs text-[var(--color-text-muted)]">o entra con tu correo</span></div>
            </div>

            <form class="space-y-3" novalidate @submit.prevent="handleLogin">
              <div>
                <label class="label" for="login-email">Correo</label>
                <input
                  id="login-email"
                  v-model="loginEmail"
                  type="email"
                  class="input"
                  :class="{ 'border-red-400': loginErrors.email }"
                  placeholder="tu@correo.com"
                  autocomplete="email"
                  required
                />
                <p v-if="loginErrors.email" class="mt-1 text-xs text-red-600">{{ loginErrors.email }}</p>
              </div>
              <div>
                <label class="label" for="login-password">Contraseña</label>
                <input
                  id="login-password"
                  v-model="loginPassword"
                  type="password"
                  class="input"
                  :class="{ 'border-red-400': loginErrors.password }"
                  placeholder="••••••••"
                  autocomplete="current-password"
                  required
                />
                <p v-if="loginErrors.password" class="mt-1 text-xs text-red-600">{{ loginErrors.password }}</p>
              </div>
              <button type="submit" class="btn btn-primary btn-block" :disabled="isLoading">
                <span v-if="isLoading" class="opacity-70">Iniciando sesión…</span>
                <span v-else>Iniciar sesión</span>
              </button>
            </form>

            <p class="text-center text-sm text-[var(--color-text-muted)] mt-6">
              ¿Primera vez?
              <button type="button" class="text-[var(--color-primary)] font-semibold hover:underline" @click="toggle">
                Crear cuenta
              </button>
            </p>
          </div>

          <!-- ============================================================ -->
          <!-- REGISTER                                                      -->
          <!-- ============================================================ -->
          <div v-else key="register">
            <div class="hidden lg:block mb-8">
              <p class="text-sm text-[var(--color-primary)] font-semibold uppercase tracking-wider">Crear cuenta</p>
              <h1 class="text-3xl font-bold mt-1">
                {{ isCompletingOAuthProfile ? 'Completa tu perfil' : 'Empieza tu camino' }}
              </h1>
              <p class="text-[var(--color-text-muted)] mt-2">
                {{ pendingRegistration ? 'Escribe el código que recibiste por correo.' : isCompletingOAuthProfile ? 'Solo falta un paso más para entrar.' : 'Es gratis y solo te toma un minuto.' }}
              </p>
            </div>
            <div class="lg:hidden text-center mb-6">
              <h1 class="text-2xl font-bold">
                {{ pendingRegistration ? 'Verifica tu correo' : isCompletingOAuthProfile ? 'Completa tu perfil' : 'Crea tu cuenta' }}
              </h1>
              <p class="text-[var(--color-text-muted)] mt-1">
                {{ pendingRegistration ? 'Ingresa tu código.' : isCompletingOAuthProfile ? 'Un paso más.' : 'Es gratis y rápido.' }}
              </p>
            </div>

            <form class="space-y-3" novalidate @submit.prevent="handleRegister">
              <div v-if="pendingRegistration" class="space-y-3">
                <p class="text-sm text-[var(--color-text-muted)]">
                  Enviamos un código a <strong class="text-[var(--color-text)]">{{ pendingRegistration.email }}</strong>.
                </p>
                <div>
                  <label class="label" for="reg-verification-code">Código de verificación</label>
                  <input
                    id="reg-verification-code"
                    v-model="verificationCode"
                    type="text"
                    inputmode="numeric"
                    pattern="[0-9]{6}"
                    maxlength="6"
                    class="input text-center tracking-[0.35em]"
                    :class="{ 'border-red-400': regErrors.verificationCode }"
                    placeholder="000000"
                    autocomplete="one-time-code"
                    required
                  />
                  <p v-if="regErrors.verificationCode" class="mt-1 text-xs text-red-600">{{ regErrors.verificationCode }}</p>
                </div>
                <button type="button" class="text-sm text-[var(--color-primary)] font-semibold hover:underline" :disabled="isLoading" @click="resendVerificationCode">
                  Reenviar código
                </button>
              </div>

              <template v-else>
              <div v-if="!isCompletingOAuthProfile">
                <label class="label" for="reg-email">Correo</label>
                <input
                  id="reg-email"
                  v-model="regEmail"
                  type="email"
                  class="input"
                  :class="{ 'border-red-400': regErrors.email }"
                  placeholder="tu@correo.com"
                  autocomplete="email"
                  required
                  maxlength="120"
                />
                <p v-if="regErrors.email" class="mt-1 text-xs text-red-600">{{ regErrors.email }}</p>
              </div>

              <div v-if="!isCompletingOAuthProfile">
                <label class="label" for="reg-password">Contraseña</label>
                <input
                  id="reg-password"
                  v-model="regPassword"
                  type="password"
                  class="input"
                  :class="{ 'border-red-400': regErrors.password }"
                  placeholder="Mínimo 8 caracteres"
                  autocomplete="new-password"
                  required
                  minlength="8"
                />
                <p v-if="regErrors.password" class="mt-1 text-xs text-red-600">{{ regErrors.password }}</p>
              </div>

              <label class="flex items-start gap-2 text-sm">
                <input
                  v-model="regTerms"
                  type="checkbox"
                  required
                  class="mt-1"
                  :class="{ 'outline outline-red-400': regErrors.terms }"
                />
                <span>
                  Acepto los
                  <a href="/terminos" target="_blank" rel="noopener noreferrer" class="text-[var(--color-primary)] underline">Términos</a>
                  y el
                  <a href="/privacidad" target="_blank" rel="noopener noreferrer" class="text-[var(--color-primary)] underline">Aviso de Privacidad</a>.
                </span>
              </label>
              <p v-if="regErrors.terms" class="mt-1 text-xs text-red-600">{{ regErrors.terms }}</p>
              </template>

              <button type="submit" class="btn btn-primary btn-block" :disabled="isLoading">
                <span v-if="isLoading" class="opacity-70">{{ pendingRegistration ? 'Verificando…' : 'Creando cuenta…' }}</span>
                <span v-else>{{ pendingRegistration ? 'Verificar y entrar' : isCompletingOAuthProfile ? 'Completar perfil' : 'Crear mi cuenta' }}</span>
              </button>
            </form>

            <p v-if="!isCompletingOAuthProfile && !pendingRegistration" class="text-center text-sm text-[var(--color-text-muted)] mt-6">
              ¿Ya tienes cuenta?
              <button type="button" class="text-[var(--color-primary)] font-semibold hover:underline" @click="toggle">
                Iniciar sesión
              </button>
            </p>
          </div>
        </Transition>
      </div>
    </main>
  </div>
</template>
