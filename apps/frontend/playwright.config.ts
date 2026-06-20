import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Keep it single-threaded to avoid DB conflicts with SQLite
  reporter: 'line',
  use: {
    baseURL: 'http://localhost:4321',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'pnpm run dev',
      url: 'http://localhost:4321',
      reuseExistingServer: !process.env.CI,
      env: {
        VITE_NEON_AUTH_URL: 'http://localhost:8000/mock-auth',
        ALLOW_MOCK_AUTH: 'true',
        PUBLIC_ALLOW_MOCK_AUTH: 'true',
        PUBLIC_API_URL: 'http://localhost:8000',
      },
    },
    {
      command: 'cd ../backend && DATABASE_URL=sqlite+aiosqlite:///./test_e2e.db ALLOW_MOCK_AUTH=true uv run fastapi run app/main.py --port 8000',
      url: 'http://localhost:8000/health',
      reuseExistingServer: !process.env.CI,
      env: {
        DATABASE_URL: 'sqlite+aiosqlite:///./test_e2e.db',
        NEON_AUTH_URL: 'http://localhost:8000/mock-auth',
        NEON_AUTH_JWKS_URL: 'http://localhost:8000/mock-auth/.well-known/jwks.json',
        ALLOW_MOCK_AUTH: 'true',
        R2_ACCOUNT_ID: 'mock_r2',
        R2_ACCESS_KEY_ID: 'mock_r2_key',
        R2_SECRET_ACCESS_KEY: 'mock_r2_secret',
        R2_PUBLIC_BASE: 'http://localhost:8000/media',
        MEDIA_JWT_SECRET: 'mock_media_jwt_secret_must_be_32_chars_long',
        FRONTEND_URL: 'http://localhost:4321',
      },
    },
  ],
});
