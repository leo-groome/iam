import { getMigrations } from 'better-auth/db/migration'
import { createAuth, createPool } from './auth.js'
import { loadEnv } from './env.js'

const env = loadEnv()
const pool = createPool(env)

// El schema debe existir antes de que search_path lo use.
await pool.query(`CREATE SCHEMA IF NOT EXISTS ${env.DB_SCHEMA}`)

const auth = createAuth(env, pool)
const { toBeCreated, toBeAdded, runMigrations } = await getMigrations(auth.options)
console.log(`[migrate] tablas nuevas: ${toBeCreated.length}, columnas nuevas: ${toBeAdded.length}`)
await runMigrations()
await pool.end()
console.log('[migrate] ok')
