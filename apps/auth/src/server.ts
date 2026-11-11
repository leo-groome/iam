import { serve } from '@hono/node-server'
import { createApp } from './app.js'
import { createAuth, createPool } from './auth.js'
import { loadEnv } from './env.js'

const env = loadEnv()
const pool = createPool(env)
const app = createApp(env, createAuth(env, pool), pool)

const server = serve({ fetch: app.fetch, port: env.PORT, hostname: '0.0.0.0' }, (info) => {
  console.log(`[auth] escuchando en :${info.port}`)
})

for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, () => {
    server.close(() => void pool.end().then(() => process.exit(0)))
  })
}
