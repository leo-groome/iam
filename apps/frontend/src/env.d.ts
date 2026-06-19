/// <reference path="../.astro/types.d.ts" />

/**
 * Typed shape for the authenticated user injected by src/middleware.ts.
 */
interface AppUser {
  id: string
  email: string
  fullName: string
  role: 'estudiante' | 'instructor' | 'admin'
  status: string
}

declare namespace App {
  interface Locals {
    /**
     * Authenticated user resolved through the backend.
     * null when the request is unauthenticated.
     */
    user: AppUser | null
  }
}
