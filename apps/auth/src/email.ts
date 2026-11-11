import { Resend } from 'resend'
import type { Env } from './env.js'

export type OtpKind = 'sign-in' | 'email-verification' | 'forget-password' | 'change-email'

const SUBJECTS: Record<OtpKind, string> = {
  'sign-in': 'Tu código para iniciar sesión',
  'email-verification': 'Verifica tu correo',
  'forget-password': 'Restablece tu contraseña',
  'change-email': 'Confirma tu nuevo correo',
}

export interface Mailer {
  sendOtp(to: string, otp: string, kind: OtpKind): Promise<void>
}

export function createMailer(env: Env): Mailer {
  if (!env.RESEND_API_KEY) {
    // Solo dev/test: loadEnv exige RESEND_API_KEY en producción, así que este
    // camino (OTP en logs) es inalcanzable allí.
    return {
      async sendOtp(to, otp, kind) {
        console.warn(`[email:dev] RESEND_API_KEY vacío. OTP ${kind} para ${to}: ${otp}`)
      },
    }
  }
  const resend = new Resend(env.RESEND_API_KEY)
  return {
    async sendOtp(to, otp, kind) {
      const { error } = await resend.emails.send({
        from: env.EMAIL_FROM,
        to,
        subject: SUBJECTS[kind],
        text: `Tu código es ${otp}. Caduca en 10 minutos. Si no lo pediste, ignora este correo.`,
      })
      if (error) throw new Error(`Resend: ${error.name}`)
    },
  }
}
