import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authService } from '@/services/auth.service';
import type { User, LoginCredentials, RegisterData } from '@/types';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('auth_token'));
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => !!token.value);
  const isAdmin = computed(() => user.value?.rol === 'admin');
  const userName = computed(() => user.value?.nombre ?? 'Usuario');
  const userInitial = computed(() => userName.value.charAt(0).toUpperCase());

  async function login(credentials: LoginCredentials) {
    loading.value = true;
    error.value = null;
    try {
      const response = await authService.login(credentials);
      user.value = response.user;
      token.value = response.token;
      localStorage.setItem('auth_token', response.token);
    } catch (e: any) {
      error.value = e.message || 'Error al iniciar sesión';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function register(data: RegisterData) {
    loading.value = true;
    error.value = null;
    try {
      const response = await authService.register(data);
      user.value = response.user;
      token.value = response.token;
      localStorage.setItem('auth_token', response.token);
    } catch (e: any) {
      error.value = e.message || 'Error al crear cuenta';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchUser() {
    if (!token.value) return;
    try {
      user.value = await authService.me();
    } catch {
      logout();
    }
  }

  function logout() {
    user.value = null;
    token.value = null;
    localStorage.removeItem('auth_token');
  }

  // Auto-fetch user on init if token exists
  if (token.value && !user.value) {
    fetchUser();
  }

  return {
    user, token, loading, error,
    isAuthenticated, isAdmin, userName, userInitial,
    login, register, fetchUser, logout,
  };
});
