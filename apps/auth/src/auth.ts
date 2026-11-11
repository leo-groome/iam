import { betterAuth } from 'better-auth'
import { emailOTP, jwt } from 'better-auth/plugins'
import { Pool } from 'pg'
import type { Env } from './env.js'
import { createMailer } from './email.js'

function sslConfig(env: Env) {
  if (env.DB_SSL === 'disable') return false
  if (env.DB_SSL === 'no-verify') return { rejectUnauthorized: false }
  return {
    rejectUnauthorized: true,
    ...(env.DB_CA_CERT ? { ca: env.DB_CA_CERT.replace(/\\n/g, '\n') } : {}),
  }
}

export function createPool(env: Env): Pool {
  return new Pool({
    connectionString: env.DATABASE_URL,
    ssl: sslConfig(env),
    // Todas las tablas de Better Auth viven en su propio schema, aisladas de las de la app.
    options: `-c search_path=${env.DB_SCHEMA}`,
    max: 10,
  })
}

export function createAuth(env: Env, pool: Pool) {
  const mailer = createMailer(env)
  const issuer = env.BETTER_AUTH_URL.replace(/\/+$/, '')
  const isProd = env.NODE_ENV === 'production'

  return betterAuth({
    appName: 'Campus IAM',
    baseURL: issuer,
    secret: env.BETTER_AUTH_SECRET,
    database: pool,
    trustedOrigins: env.TRUSTED_ORIGINS,
    emailAndPassword: {
      enabled: true,
      minPasswordLength: 8,
      requireEmailVerification: true,
      autoSignIn: false,
    },
    // Tras verificar el OTP del registro, el usuario queda con sesión (el front pide el JWT).
    emailVerification: { autoSignInAfterVerification: true },
    socialProviders:
      env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET
        ? { google: { clientId: env.GOOGLE_CLIENT_ID, clientSecret: env.GOOGLE_CLIENT_SECRET } }
        : {},
    rateLimit: { enabled: true, storage: 'database', window: 60, max: 60 },
    advanced: {
      useSecureCookies: isProd,
      ...(env.COOKIE_DOMAIN
        ? { crossSubDomainCookies: { enabled: true, domain: env.COOKIE_DOMAIN } }
        : {}),
    },
    plugins: [
      emailOTP({
        otpLength: 6,
        expiresIn: 600,
        allowedAttempts: 3,
        sendVerificationOnSignUp: true,
        async sendVerificationOTP({ email, otp, type }) {
          // Sin await: evita timing de enumeración de usuarios.
          void mailer.sendOtp(email, otp, type).catch((err: unknown) => {
            console.error('[email] fallo enviando OTP', { type, err: String(err) })
          })
        },
      }),
      // JWT de 15 min firmado con EdDSA; el backend FastAPI lo valida vía JWKS.
      jwt({
        jwt: {
          issuer,
          audience: issuer,
          expirationTime: '15m',
          definePayload: ({ user }) => ({
            email: user.email,
            name: user.name,
            email_verified: user.emailVerified,
          }),
        },
      }),
    ],
  })
}

export type Auth = ReturnType<typeof createAuth>
