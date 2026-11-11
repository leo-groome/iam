import { Hono } from 'hono'
import { cors } from 'hono/cors'
import type { Pool } from 'pg'
import type { Auth } from './auth.js'
import type { Env } from './env.js'

export function createApp(env: Env, auth: Auth, pool: Pool) {
  const app = new Hono()

  app.get('/health', async (c) => {
    try {
      await pool.query('SELECT 1')
      return c.json({ status: 'ok' })
    } catch {
      return c.json({ status: 'degraded' }, 503)
    }
  })

  app.use(
    '/api/auth/*',
    cors({
      origin: (origin) => (env.TRUSTED_ORIGINS.includes(origin) ? origin : null),
      allowMethods: ['GET', 'POST', 'OPTIONS'],
      allowHeaders: ['Content-Type', 'Authorization'],
      exposeHeaders: ['set-auth-jwt'],
      credentials: true,
      maxAge: 600,
    }),
  )
  app.on(['GET', 'POST'], '/api/auth/*', (c) => auth.handler(c.req.raw))

  return app
}
