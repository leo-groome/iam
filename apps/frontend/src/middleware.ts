/**
 * Astro SSR middleware — auth guard for all server-rendered pages.
 *
 * Runs ONLY on SSR pages (those with `export const prerender = false`).
 * Astro never invokes middleware for statically pre-rendered pages.
 *
 * Security model:
 * - JWT validation is delegated to the backend /auth/me endpoint.
 *   Errors -> user = null, never 500.
 * - Private route access without a valid session → 302 to /registro?next=…
 * - /admin without admin|instructor role → 403 (no redirect to avoid
 *   leaking that an admin panel exists to unauthenticated users).
 * - Authenticated users hitting /registro → 302 to /catalogo (idempotent).
 */

import { defineMiddleware } from 'astro:middleware'
import { getNeonUserFromRequest } from '@/lib/neon-server'

/**
 * Pathname prefixes that require an authenticated session.
 */
const PRIVATE_PREFIXES = ['/curso', '/perfil', '/admin', '/catalogo'] as const

/**
 * Pathnames where an already-authenticated user should NOT land.
 */
const AUTH_ONLY_ROUTES = ['/registro'] as const

function isPrivateRoute(pathname: string): boolean {
  return PRIVATE_PREFIXES.some((prefix) => pathname.startsWith(prefix))
}

function isAuthOnlyRoute(pathname: string): boolean {
  return AUTH_ONLY_ROUTES.some((route) => pathname === route || pathname.startsWith(route + '?'))
}

export const onRequest = defineMiddleware(async (context, next) => {
  const url = new URL(context.request.url)
  const { pathname } = url

  // 1. Validate session server-side — errors are swallowed, return null
  const user = await getNeonUserFromRequest(context.request)
  context.locals.user = user

  // 2. Private route guard
  if (isPrivateRoute(pathname) && !user) {
    const nextParam = encodeURIComponent(pathname + url.search)
    return context.redirect(`/registro?next=${nextParam}`, 302)
  }

  // 3. Admin/instructor role guard — only fires when user IS authenticated
  //    (unauthenticated hits are caught above; no 403 leakage to anon users)
  if (
    pathname.startsWith('/admin') &&
    user &&
    user.role !== 'admin' &&
    user.role !== 'instructor'
  ) {
    return new Response(
      JSON.stringify({ error: 'Forbidden', message: 'Acceso restringido a administradores.' }),
      { status: 403, headers: { 'Content-Type': 'application/json' } },
    )
  }

  // 4. Redirect authenticated users away from auth-only pages
  if (isAuthOnlyRoute(pathname) && user) {
    return context.redirect('/catalogo', 302)
  }

  return next()
})
