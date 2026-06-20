import { api } from './api';
import type { AuthResponse, LoginCredentials, RegisterData, User } from '@/types';

/**
 * Auth service - abstracción sobre las llamadas API de autenticación.
 * Actualmente devuelve datos mock. Cuando el backend esté listo,
 * descomentar las llamadas reales y eliminar los mocks.
 */
export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // TODO: Conectar con backend real
    // return api.post<AuthResponse>('/auth/login', credentials);
    return {
      user: { id: '1', nombre: 'Alex Hernández', email: credentials.email, edad: 28, rol: 'estudiante' },
      token: 'mock-jwt-token',
    };
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    // TODO: Conectar con backend real
    // return api.post<AuthResponse>('/auth/register', data);
    return {
      user: { id: '2', nombre: data.nombre, email: data.email, edad: 18, rol: 'estudiante' },
      token: 'mock-jwt-token',
    };
  },

  async me(): Promise<User> {
    // TODO: Conectar con backend real
    // return api.get<User>('/auth/me');
    return { id: '1', nombre: 'Alex Hernández', email: 'alex@correo.com', edad: 28, rol: 'estudiante' };
  },

  async logout(): Promise<void> {
    // TODO: Conectar con backend real
    // return api.post('/auth/logout');
    localStorage.removeItem('auth_token');
  },
};
