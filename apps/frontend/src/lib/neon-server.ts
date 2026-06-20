import { AUTH_TOKEN_COOKIE } from './auth-constants'

const API_BASE =
  (typeof import.meta !== 'undefined' && (import.meta.env?.PUBLIC_API_URL as string | undefined)) ||
  'http://localhost:8000'

export interface AppUser {
  id: string
  email: string
  fullName: string
  role: 'estudiante' | 'instructor' | 'admin'
  status: string
}

function getCookie(request: Request, name: string): string | null {
  const cookieHeader = request.headers.get('cookie')
  if (!cookieHeader) return null

  for (const part of cookieHeader.split(';')) {
    const [key, ...rest] = part.trim().split('=')
    if (key === name) return decodeURIComponent(rest.join('='))
  }

  return null
}

function mockUserFromToken(token: string): AppUser | null {
  if (!token.startsWith('mock-token:')) return null

  const parts = token.split(':')
  const role = parts[4] === 'student' ? 'estudiante' : parts[4]

  return {
    id: parts[1] || 'mock_sub',
    email: parts[2] || 'mock@example.com',
    fullName: parts[3] || 'Mock User',
    role: role === 'admin' || role === 'instructor' ? role : 'estudiante',
    status: 'activo',
  }
}

export async function getNeonUserFromRequest(request: Request): Promise<AppUser | null> {
  const token =
    getCookie(request, AUTH_TOKEN_COOKIE) ||
    request.headers.get('Authorization')?.replace('Bearer ', '')

  if (!token) return null

  if (import.meta.env.PUBLIC_ALLOW_MOCK_AUTH === 'true') {
    const mockUser = mockUserFromToken(token)
    if (mockUser) return mockUser
  }

  try {
    const res = await fetch(new URL('/api/v1/auth/me', API_BASE), {
      headers: {
        Accept: 'application/json',
        Authorization: `Bearer ${token}`,
      },
    })

    if (!res.ok) return null

    const user = (await res.json()) as {
      id: string
      email: string
      full_name: string
      role: string
      status: string
    }

    return {
      id: user.id,
      email: user.email,
      fullName: user.full_name,
      role:
        user.role === 'admin' || user.role === 'instructor' || user.role === 'estudiante'
          ? user.role
          : 'estudiante',
      status: user.status,
    }
  } catch (err) {
    console.error('[neon-server] Auth lookup failed:', err)
    return null
  }
}
