/**
 * Typed HTTP client for the IAM backend API (client-side SPA only).
 *
 * Usage (Vue component):
 *   const courses = await apiGet('/api/v1/courses')
 *
 * Token resolution: asks Neon Auth for a fresh JWT via getAuthToken().
 *
 * All 4xx/5xx responses throw ApiError with a typed `code` field.
 * Worker R2 media streams use `mediaFetch(url, token)` — token in Bearer header only.
 */

import type { paths, components } from './types.gen'
import { AUTH_TOKEN_COOKIE } from './auth-constants'
import { getAuthToken } from './auth-client'

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const API_BASE =
  (typeof import.meta !== 'undefined' && (import.meta.env?.PUBLIC_API_URL as string | undefined)) ||
  'http://localhost:8000'

// ---------------------------------------------------------------------------
// ApiError
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  readonly status: number
  readonly code: ApiErrorCode
  readonly body: unknown

  constructor(status: number, code: ApiErrorCode, message: string, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.body = body
  }
}

export type ApiErrorCode =
  | 'UNAUTHORIZED'
  | 'FORBIDDEN'
  | 'NOT_FOUND'
  | 'UNPROCESSABLE'
  | 'RATE_LIMITED'
  | 'SERVER_ERROR'
  | 'NETWORK_ERROR'
  | 'UNKNOWN'

function statusToCode(status: number): ApiErrorCode {
  if (status === 401) return 'UNAUTHORIZED'
  if (status === 403) return 'FORBIDDEN'
  if (status === 404) return 'NOT_FOUND'
  if (status === 422) return 'UNPROCESSABLE'
  if (status === 429) return 'RATE_LIMITED'
  if (status >= 500) return 'SERVER_ERROR'
  return 'UNKNOWN'
}

async function throwApiError(res: Response): Promise<never> {
  let body: unknown
  let message = `HTTP ${res.status}`

  try {
    body = await res.json()
    // FastAPI surfaces errors as { detail: string | object }
    if (body && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail: unknown }).detail
      if (typeof detail === 'string') message = detail
      else if (Array.isArray(detail) && detail.length > 0) {
        // Pydantic validation errors: [{loc, msg, type}]
        message = detail.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join('; ')
      }
    }
  } catch {
    // Non-JSON error body — use status text
    message = res.statusText || message
  }

  throw new ApiError(res.status, statusToCode(res.status), message, body)
}

// ---------------------------------------------------------------------------
// Token extraction
// ---------------------------------------------------------------------------

async function resolveToken(): Promise<string | null> {
  return getAuthToken()
}

// ---------------------------------------------------------------------------
// Core apiFetch
// ---------------------------------------------------------------------------

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface ApiFetchOptions {
  /** HTTP method. */
  method?: HttpMethod
  /** Path params to interpolate into the URL template (e.g. { slug: 'mi-curso' }). */
  params?: Record<string, string>
  /** Query string parameters. */
  query?: Record<string, string | number | boolean | null | undefined>
  /** Request body — will be JSON.stringified. */
  body?: unknown
}

/**
 * Low-level typed fetch wrapper.
 *
 * `path` is a key of the generated `paths` interface — TypeScript will catch
 * unknown routes at compile time.
 */
export async function apiFetch<P extends keyof paths>(
  path: P,
  options: ApiFetchOptions = {},
): Promise<unknown> {
  const { method = 'GET', params, query, body } = options

  // 1. Interpolate path params
  let resolvedPath: string = path as string
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      resolvedPath = resolvedPath.replace(`{${key}}`, encodeURIComponent(value))
    }
  }

  // 2. Build URL
  const url = new URL(resolvedPath, API_BASE)
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== null && value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  // 3. Build headers
  const headers: Record<string, string> = {
    Accept: 'application/json',
  }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  const token = await resolveToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // 4. Fetch
  let res: Response
  try {
    res = await fetch(url.toString(), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    throw new ApiError(0, 'NETWORK_ERROR', (err as Error)?.message ?? 'Network error', undefined)
  }

  // 5. Handle errors
  if (!res.ok) {
    await throwApiError(res)
  }

  // 6. Parse success body (204 No Content has no body)
  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return undefined
  }

  const contentType = res.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    return res.json()
  }

  return res.text()
}

// ---------------------------------------------------------------------------
// Typed shortcut helpers
// ---------------------------------------------------------------------------

type GetOptions = Omit<ApiFetchOptions, 'method' | 'body'>
type MutateOptions = Omit<ApiFetchOptions, 'method'>

export async function apiGet<P extends keyof paths>(
  path: P,
  options: GetOptions = {},
): Promise<unknown> {
  return apiFetch(path, { ...options, method: 'GET' })
}

export async function apiPost<P extends keyof paths>(
  path: P,
  options: MutateOptions = {},
): Promise<unknown> {
  return apiFetch(path, { ...options, method: 'POST' })
}

export async function apiPatch<P extends keyof paths>(
  path: P,
  options: MutateOptions = {},
): Promise<unknown> {
  return apiFetch(path, { ...options, method: 'PATCH' })
}

export async function apiPut<P extends keyof paths>(
  path: P,
  options: MutateOptions = {},
): Promise<unknown> {
  return apiFetch(path, { ...options, method: 'PUT' })
}

export async function apiDelete<P extends keyof paths>(
  path: P,
  options: MutateOptions = {},
): Promise<unknown> {
  return apiFetch(path, { ...options, method: 'DELETE' })
}

export async function apiBlob(
  path: keyof paths | string,
  options: GetOptions = {},
): Promise<{ blob: Blob; filename: string | null }> {
  const { params, query } = options
  let resolvedPath = path as string
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      resolvedPath = resolvedPath.replace(`{${key}}`, encodeURIComponent(value))
    }
  }

  const url = new URL(resolvedPath, API_BASE)
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== null && value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    }
  }

  const headers: Record<string, string> = { Accept: '*/*' }
  const token = await resolveToken()
  if (token) headers.Authorization = `Bearer ${token}`

  let res: Response
  try {
    res = await fetch(url.toString(), { method: 'GET', headers })
  } catch (err) {
    throw new ApiError(0, 'NETWORK_ERROR', (err as Error)?.message ?? 'Network error', undefined)
  }
  if (!res.ok) await throwApiError(res)

  const disposition = res.headers.get('content-disposition')
  const filename = disposition?.match(/filename="?([^"]+)"?/i)?.[1] ?? null
  return { blob: await res.blob(), filename }
}

// ---------------------------------------------------------------------------
// Media Worker fetch helper (R2 via Cloudflare Worker)
// ---------------------------------------------------------------------------

/**
 * Fetch media from the CF Worker / R2 edge using Bearer auth.
 *
 * SECURITY: token is NEVER sent as a query string parameter.
 * Pass it exclusively in the Authorization header.
 *
 * @param url    - Full media URL returned by /api/v1/media/play-token.
 * @param token  - Short-lived JWT from PlayTokenResponse.token.
 * @returns      - Blob of the media content (video, PDF, image).
 */
export async function mediaFetch(url: string, token: string): Promise<Blob> {
  let res: Response
  try {
    res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
  } catch (err) {
    throw new ApiError(0, 'NETWORK_ERROR', (err as Error)?.message ?? 'Media fetch failed')
  }

  if (!res.ok) {
    await throwApiError(res)
  }

  return res.blob()
}

/**
 * Stream variant of mediaFetch — returns the raw Response body as a ReadableStream.
 * Useful for large video files where you want to pipe directly to a <video> element
 * via a Blob URL rather than loading the entire file into memory.
 */
export async function mediaStream(url: string, token: string): Promise<Response> {
  let res: Response
  try {
    res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
  } catch (err) {
    throw new ApiError(0, 'NETWORK_ERROR', (err as Error)?.message ?? 'Media stream failed')
  }

  if (!res.ok) {
    await throwApiError(res)
  }

  return res
}

// ---------------------------------------------------------------------------
// Domain type re-exports (friendly aliases)
// ---------------------------------------------------------------------------

export type User = components['schemas']['UserPublic']
export type SyncRequest = components['schemas']['SyncRequest']

export type Course = components['schemas']['CourseCard']
export type CourseList = components['schemas']['CourseCardListResponse']
export type CourseDetail = components['schemas']['CourseDetail']
export type CourseProgress = components['schemas']['CourseProgressResponse']
export type EnrollResponse = components['schemas']['EnrollResponse']

export type ExamResponse = components['schemas']['ExamResponse']
export type QuestionOut = components['schemas']['QuestionOut']
export type OptionOut = components['schemas']['OptionOut']

export type TopicDetail = components['schemas']['TopicResponse']
export type PlayTokenRequest = components['schemas']['PlayTokenRequest']
export type PlayTokenResponse = components['schemas']['PlayTokenResponse']

export type CertificatePublic = components['schemas']['CertificatePublic']
export type DashboardResponse = components['schemas']['DashboardResponse']
