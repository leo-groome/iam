import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAuthToken,
  refreshAuthTokenCookie,
  verifyEmailOtp,
  isMockAuthAllowed,
  logout as authClientLogout,
  authClient,
  AUTH_TOKEN_COOKIE,
} from '@/lib/auth-client'
import { apiGet, apiPost, ApiError } from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AppUser {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'instructor' | 'estudiante'
  status: string
}

// Onboarding answers bundled into /auth/sync. `nombre` is dropped client-side
// (it maps to full_name); the rest mirror the backend OnboardingIn schema.
export interface OnboardingPayload {
  edad: string
  sexo: string
  diocesis: string
  ciudad: string
  parroquia: string
  entorno: string
  pastoral: string
  extra?: Record<string, unknown>
}

// ---------------------------------------------------------------------------
// Mock token parser
// Format: mock-token:<sub>:<email>:<name>:<role>
// ---------------------------------------------------------------------------

function parseMockToken(token: string): AppUser | null {
  if (!token.startsWith('mock-token:')) return null
  const parts = token.split(':')
  // parts[0] = 'mock-token', [1] = sub, [2] = email, [3] = name, [4] = role
  if (parts.length < 5) return null
  const [, sub, email, name, role] = parts
  return {
    id: sub ?? 'mock_id',
    email: email ?? 'mock@example.com',
    full_name: name ?? 'Mock User',
    role: (role === 'admin' ? 'admin' : role === 'instructor' ? 'instructor' : 'estudiante') as AppUser['role'],
    status: 'active',
  }
}

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  for (const part of document.cookie.split(';')) {
    const [key, ...rest] = part.trim().split('=')
    if (key === name) return decodeURIComponent(rest.join('='))
  }
  return null
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AppUser | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)
  const initialized = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isInstructor = computed(() => user.value?.role === 'instructor' || user.value?.role === 'admin')

  // ---------------------------------------------------------------------------
  // fetchMe — hits /api/v1/auth/me to populate user
  // ---------------------------------------------------------------------------
  async function fetchMe(): Promise<void> {
    try {
      const data = await apiGet('/api/v1/auth/me')
      user.value = data as AppUser
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // User authenticated but not yet synced — keep token, leave user=null
        return
      }
      // 401 / other errors: clear state
      user.value = null
      token.value = null
      throw err
    }
  }

  // ---------------------------------------------------------------------------
  // init — called once on app bootstrap
  // ---------------------------------------------------------------------------
  async function init(): Promise<void> {
    if (initialized.value) return

    loading.value = true
    error.value = null

    try {
      // Dev mock path
      if (isMockAuthAllowed()) {
        const mockCookie = getCookie(AUTH_TOKEN_COOKIE)
        if (mockCookie?.startsWith('mock-token:')) {
          const parsed = parseMockToken(mockCookie)
          if (parsed) {
            user.value = parsed
            token.value = mockCookie
            return
          }
        }
      }

      // Real auth path
      const resolvedToken = await getAuthToken()
      if (resolvedToken) {
        token.value = resolvedToken
        await fetchMe()
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Auth init failed'
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  // ---------------------------------------------------------------------------
  // login
  // ---------------------------------------------------------------------------
  async function login(email: string, password: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const { error: signInError } = await authClient.signIn.email({ email, password })
      if (signInError) throw signInError
      const t = await refreshAuthTokenCookie()
      token.value = t
      await fetchMe()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ---------------------------------------------------------------------------
  // register
  // ---------------------------------------------------------------------------
  async function register(
    email: string,
    password: string,
    name: string,
  ): Promise<{ status: 'pending_verification' }> {
    loading.value = true
    error.value = null
    try {
      const { error: signUpError } = await authClient.signUp.email({ email, password, name })
      if (signUpError) throw signUpError
      return { status: 'pending_verification' }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Register failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ---------------------------------------------------------------------------
  // verifyOtp — verify email OTP and sync profile to backend
  // ---------------------------------------------------------------------------
  async function verifyOtp(
    email: string,
    otp: string,
    full_name: string,
    birth_date: string,
    onboarding?: OnboardingPayload,
  ): Promise<void> {
    loading.value = true
    error.value = null
    try {
      // Try OTP verify endpoint first
      const verifiedToken = await verifyEmailOtp(email, otp)

      if (!verifiedToken) {
        // Fallback: sign in via emailOtp
        const { error: otpError } = await authClient.signIn.emailOtp({ email, otp })
        if (otpError) throw otpError
      }

      const t = await refreshAuthTokenCookie()
      token.value = t

      await apiPost('/api/v1/auth/sync', {
        body: { full_name, birth_date, onboarding: onboarding ?? null },
      })

      // Onboarding cache is single-use: clear it once persisted.
      if (onboarding) sessionStorage.removeItem('onboardingData')

      await fetchMe()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Verification failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ---------------------------------------------------------------------------
  // logout
  // ---------------------------------------------------------------------------
  async function logout(): Promise<void> {
    try {
      await authClientLogout()
    } finally {
      user.value = null
      token.value = null
    }
    // Caller is responsible for redirect
  }

  return {
    // state
    user,
    token,
    loading,
    initialized,
    error,
    // getters
    isAuthenticated,
    isAdmin,
    isInstructor,
    // actions
    init,
    login,
    register,
    verifyOtp,
    fetchMe,
    logout,
  }
})
