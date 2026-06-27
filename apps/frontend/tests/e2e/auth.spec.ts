import { test, expect } from '@playwright/test';

test.describe('IAM Training Platform E2E Tests', () => {

  test('Landing page loads and displays login screen', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Plataforma de Formación/);
    
    // Check that login form elements are present
    const emailInput = page.locator('#login-email');
    const passwordInput = page.locator('#login-password');
    const submitBtn = page.locator('button[type="submit"]', { hasText: 'Iniciar sesión' });
    
    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(submitBtn).toBeVisible();
  });

  test('Registration (Sign Up) flow creates user and redirects to catalog', async ({ context, page }) => {
    // Stub Neon Auth signUp/token calls to bypass network calls
    await context.addInitScript(() => {
      let stubbed = false;
      Object.defineProperty(window, 'authClient', {
        configurable: true,
        enumerable: true,
        get() {
          return this._authClient;
        },
        set(val) {
          this._authClient = val;
          if (val && !stubbed) {
            stubbed = true;
            val.signUp = {
              email: async (credentials: any) => {
                document.cookie = `neon-auth-token=mock-token:mock_student_id:${credentials.email}:Student User:student; path=/; max-age=3600`;
                return { data: { user: { id: 'mock_student_id' } }, error: null };
              },
            };
            val.token = {
              get: () => {
                return { data: { token: 'mock-token:mock_student_id:new_student@example.com:Student User:student' }, error: null };
              }
            };
          }
        }
      });
      window.sessionStorage.setItem('onboardingData', JSON.stringify({
        nombre: 'Student User',
        edad: '18-25',
        sexo: 'Hombre',
        diocesis: 'Aguascalientes',
        ciudad: 'Aguascalientes',
        parroquia: 'San Jose',
        entorno: 'Urbana',
        pastoral: 'IAM'
      }));
      window.localStorage.setItem('hasCompletedOnboarding', 'true');
    });

    await page.goto('/registro');
    await expect(page.locator('[data-auth-ready="true"]')).toBeVisible();

    // Fill in registration form
    await page.locator('#reg-email').fill('new_student@example.com');
    await page.locator('#reg-password').fill('password123');
    await page.locator('form input[type="checkbox"]').check();

    // Click register button
    await page.locator('button[type="submit"]').click();

    // Should redirect to /catalogo and show catalog page
    await page.waitForURL('**/catalogo');
    await expect(page.locator('main h1')).toContainText('Cursos');
    
    // The seeded course "Comunicación Empática" should be visible
    await expect(page.locator('h3', { hasText: 'Comunicación Empática' })).toBeVisible();
  });

  test('Direct access to catalog as student using mock cookie', async ({ context, page }) => {
    // Go to landing first to establish the origin for cookies
    await page.goto('/');
    
    // Inject mock student token cookie directly
    await context.addCookies([
      {
        name: 'neon-auth-token',
        value: 'mock-token:mock_student_id:student@example.com:Student User:student',
        domain: 'localhost',
        path: '/',
      }
    ]);

    await page.goto('/catalogo');
    await expect(page.locator('main h1')).toContainText('Cursos');
    await expect(page.locator('text=Cursos disponibles')).toBeVisible();
    await expect(page.locator('h3', { hasText: 'Comunicación Empática' })).toBeVisible();
  });

  test('Direct access to admin dashboard as admin using mock cookie', async ({ context, page }) => {
    // Go to landing first to establish the origin for cookies
    await page.goto('/');
    
    // Inject mock admin token cookie directly
    await context.addCookies([
      {
        name: 'neon-auth-token',
        value: 'mock-token:mock_admin_id:admin@example.com:Admin User:admin',
        domain: 'localhost',
        path: '/',
      }
    ]);

    await page.goto('/admin');
    await expect(page.locator('main h1')).toContainText('Dashboard');
    
    // Navigate to courses list
    await page.locator('a', { hasText: 'Cursos' }).first().click();
    await page.waitForURL('**/admin/cursos');
    
    // Seeded course should be in list
    await expect(page.locator('text=Comunicación Empática')).toBeVisible();
  });
});
