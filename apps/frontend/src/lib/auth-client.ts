import { createAuthClient } from 'better-auth/client'
import { emailOTPClient, jwtClient } from 'better-auth/client/plugins'
import { AUTH_TOKEN_COOKIE } from './auth-constants'

export { AUTH_TOKEN_COOKIE } from './auth-constants'

// Origen del servicio apps/auth (Better Auth), p. ej. http://localhost:3001
const authUrl =
  (import.meta.env.PUBLIC_AUTH_URL as string | undefined) ||
  (import.meta.env.VITE_AUTH_URL as string | undefined)

const normalizedAuthUrl = authUrl?.replace(/\/+$/, '')

export const authClient = createAuthClient({
  baseURL: normalizedAuthUrl ?? 'http://localhost:3001',
  fetchOptions: { credentials: 'include' },
  plugins: [emailOTPClient(), jwtClient()],
})

export function hasAuthConfig(): boolean {
  return Boolean(normalizedAuthUrl)
}

export function assertAuthConfigured(): void {
  if (!normalizedAuthUrl) {
    throw new Error('[auth-client] Missing VITE_AUTH_URL or PUBLIC_AUTH_URL; restart the dev server after setting it')
  }
}

/** Base de los endpoints de Better Auth (`<origen>/api/auth`). */
export function getAuthUrl(): string {
  assertAuthConfigured()
  return `${normalizedAuthUrl}/api/auth`
}

async function throwAuthResponse(res: Response): Promise<never> {
  let message = `Auth HTTP ${res.status}`
  try {
    const body = await res.json()
    if (body?.message) message = body.message
    else if (body?.error) message = body.error
  } catch {
    // Keep status-only message for non-JSON responses.
  }
  throw new Error(message)
}

export async function verifyEmailOtp(email: string, otp: string): Promise<string | null> {
  const res = await fetch(`${getAuthUrl()}/email-otp/verify-email`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ email, otp }),
  })

  if (!res.ok) await throwAuthResponse(res)
  const data = await res.json().catch(() => null)
  return typeof data?.token === 'string' ? data.token : null
}

export async function sendEmailVerificationOtp(email: string): Promise<void> {
  const res = await fetch(`${getAuthUrl()}/email-otp/send-verification-otp`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ email, type: 'email-verification' }),
  })

  if (!res.ok) await throwAuthResponse(res)
}

export async function requestPasswordResetOtp(email: string): Promise<void> {
  const res = await fetch(`${getAuthUrl()}/email-otp/request-password-reset`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ email }),
  })

  if (!res.ok) await throwAuthResponse(res)
}

export async function resetPasswordWithOtp(
  email: string,
  otp: string,
  password: string,
): Promise<void> {
  const res = await fetch(`${getAuthUrl()}/email-otp/reset-password`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ email, otp, password }),
  })

  if (!res.ok) await throwAuthResponse(res)
}

export function isMockAuthAllowed(): boolean {
  return import.meta.env.PUBLIC_ALLOW_MOCK_AUTH === 'true'
}

function cookieOptions(maxAge: number): string {
  const secure = typeof window !== 'undefined' && window.location.protocol === 'https:' ? '; Secure' : ''
  return `path=/; max-age=${maxAge}; SameSite=Lax${secure}`
}

function parseJwtHeader(token: string): unknown {
  try {
    const [header] = token.split('.')
    if (!header) return null
    const padded = header.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (header.length % 4)) % 4)
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}

export function isJwtLike(token: string | null | undefined): token is string {
  if (!token) return false
  if (token.split('.').length !== 3) return false
  const header = parseJwtHeader(token)
  return Boolean(header && typeof header === 'object' && 'alg' in header)
}

function isCookieAuthToken(token: string): boolean {
  return token.startsWith('mock-token:') || isJwtLike(token)
}

export function setAuthTokenCookie(token: string): void {
  if (typeof document === 'undefined') return
  if (!isCookieAuthToken(token)) {
    clearAuthTokenCookie()
    throw new Error('Auth service did not return a backend JWT')
  }
  document.cookie = `${AUTH_TOKEN_COOKIE}=${encodeURIComponent(token)}; ${cookieOptions(60 * 15)}`
}

export function clearAuthTokenCookie(): void {
  if (typeof document === 'undefined') return
  document.cookie = `${AUTH_TOKEN_COOKIE}=; ${cookieOptions(0)}`
}

export function setMockAuthToken(email: string, name = 'Mock User', role = 'student'): string {
  const sub = role === 'admin' ? 'mock_admin_id' : 'mock_student_id'
  const token = `mock-token:${sub}:${email}:${name}:${role}`
  setAuthTokenCookie(token)
  return token
}

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  for (const part of document.cookie.split(';')) {
    const [key, ...rest] = part.trim().split('=')
    if (key === name) return decodeURIComponent(rest.join('='))
  }
  return null
}

export async function refreshAuthTokenCookie(): Promise<string> {
  if (isMockAuthAllowed()) {
    const mockToken = getCookie(AUTH_TOKEN_COOKIE)
    if (mockToken?.startsWith('mock-token:')) return mockToken
  }

  assertAuthConfigured()

  // JWT de 15 min emitido por el plugin jwt de Better Auth (requiere sesión por cookie).
  const { data, error } = await authClient.token().catch((err) => {
    throw new Error(`No pudimos obtener el JWT del servicio de auth: ${(err as Error).message}`)
  })
  if (error) throw error
  if (!data?.token) throw new Error('No auth token returned')
  if (!isJwtLike(data.token)) throw new Error('Auth service did not return a backend JWT')

  setAuthTokenCookie(data.token)
  return data.token
}

export async function getAuthToken(): Promise<string | null> {
  const existingToken = getCookie(AUTH_TOKEN_COOKIE)
  if (existingToken?.startsWith('mock-token:')) return existingToken
  if (isJwtLike(existingToken)) return existingToken
  if (existingToken) clearAuthTokenCookie()

  try {
    return await refreshAuthTokenCookie()
  } catch {
    return null
  }
}

if (typeof window !== 'undefined' && isMockAuthAllowed()) {
  ;(window as any).authClient = authClient
}

export async function logout(): Promise<void> {
  try {
    assertAuthConfigured()
    await authClient.signOut()
  } catch (err) {
    console.error('[auth-client] signOut error:', err)
  } finally {
    clearAuthTokenCookie()
  }
  window.location.href = '/'
}
