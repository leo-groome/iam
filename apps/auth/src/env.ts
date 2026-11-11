import { z } from 'zod'

const csv = z
  .string()
  .default('')
  .transform((v) =>
    v
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
  )

const schema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().positive().default(3001),
  // URL pública del servicio de auth (sin path). Es el `iss`/`aud` de los JWT.
  BETTER_AUTH_URL: z.url(),
  BETTER_AUTH_SECRET: z.string().min(32, 'BETTER_AUTH_SECRET debe tener >= 32 caracteres'),
  DATABASE_URL: z.string().min(1),
  // require = TLS verificando el certificado (usa DB_CA_CERT si el CA no es público).
  // disable = red privada/local. no-verify = TLS sin verificar: solo como excepción consciente.
  DB_SSL: z.enum(['require', 'no-verify', 'disable']).default('require'),
  // CA en PEM (puede venir con \n escapados) para verificar el servidor Postgres.
  DB_CA_CERT: z.string().optional(),
  DB_SCHEMA: z
    .string()
    .regex(/^[a-z_][a-z0-9_]*$/)
    .default('auth'),
  // Orígenes de las apps (frontend, landing) autorizados a usar el servicio.
  TRUSTED_ORIGINS: csv,
  // Opcional: ".valtaoperative.com" para compartir cookie entre subdominios.
  COOKIE_DOMAIN: z.string().optional(),
  RESEND_API_KEY: z.string().optional(),
  EMAIL_FROM: z.string().default('Campus IAM <no-reply@localhost>'),
  GOOGLE_CLIENT_ID: z.string().optional(),
  GOOGLE_CLIENT_SECRET: z.string().optional(),
})

export type Env = z.infer<typeof schema>

export function loadEnv(source: NodeJS.ProcessEnv = process.env): Env {
  const env = schema.parse(source)
  if (env.NODE_ENV === 'production' && !env.RESEND_API_KEY) {
    throw new Error('RESEND_API_KEY es obligatorio en producción')
  }
  return env
}
