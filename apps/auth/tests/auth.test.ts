import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { Pool } from 'pg'
import { createApp } from '../src/app.js'
import { createAuth, createPool } from '../src/auth.js'
import { loadEnv } from '../src/env.js'

// Requiere Postgres (en CI: service container; en local: `docker compose up db`).
const DATABASE_URL = process.env.TEST_DATABASE_URL ?? process.env.DATABASE_URL

const env = loadEnv({
  NODE_ENV: 'test',
  BETTER_AUTH_URL: 'http://localhost:3001',
  BETTER_AUTH_SECRET: 'test-secret-test-secret-test-secret-0000',
  DATABASE_URL: DATABASE_URL ?? 'postgresql://x',
  DB_SSL: 'disable',
  DB_SCHEMA: 'auth_test',
  TRUSTED_ORIGINS: 'http://localhost:4321',
} as NodeJS.ProcessEnv)

describe.skipIf(!DATABASE_URL)('auth service', () => {
  let pool: Pool
  let app: ReturnType<typeof createApp>

  beforeAll(async () => {
    pool = createPool(env)
    await pool.query('DROP SCHEMA IF EXISTS auth_test CASCADE')
    await pool.query('CREATE SCHEMA auth_test')
    const auth = createAuth(env, pool)
    const { getMigrations } = await import('better-auth/db/migration')
    await (await getMigrations(auth.options)).runMigrations()
    app = createApp(env, auth, pool)
  })

  afterAll(async () => {
    await pool?.query('DROP SCHEMA IF EXISTS auth_test CASCADE')
    await pool?.end()
  })

  it('health ok', async () => {
    const res = await app.request('/health')
    expect(res.status).toBe(200)
  })

  it('expone JWKS EdDSA para el backend', async () => {
    // El JWKS se genera perezosamente en el primer uso.
    const res = await app.request('/api/auth/jwks')
    expect(res.status).toBe(200)
    const body = (await res.json()) as { keys: { alg?: string; crv?: string }[] }
    expect(body.keys.length).toBeGreaterThan(0)
    expect(body.keys[0]?.crv).toBe('Ed25519')
  })

  it('rechaza sign-in con credenciales inexistentes', async () => {
    const res = await app.request('/api/auth/sign-in/email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:4321' },
      body: JSON.stringify({ email: 'nadie@example.com', password: 'incorrecta123' }),
    })
    expect(res.status).toBe(401)
  })

  it('CORS: no refleja orígenes no confiables', async () => {
    const res = await app.request('/api/auth/jwks', { headers: { Origin: 'https://evil.example' } })
    expect(res.headers.get('access-control-allow-origin')).toBeNull()
  })
})
