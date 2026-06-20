// ===== Auth Types =====
export interface User {
  id: string;
  email: string;
  full_name: string;
  birth_date?: string;
  role: 'admin' | 'instructor' | 'estudiante';
  status: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  nombre: string;
  email: string;
  password: string;
  fechaNacimiento: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

// ===== Course Types =====
export type TemaStatus = 'bloqueado' | 'disponible' | 'aprobado' | 'en_repaso';
export type TemaType = 'video' | 'pdf' | 'imagen' | 'texto';

export interface Tema {
  id: string;
  title: string;
  type: TemaType;
  duration: string;
  hasExam: boolean;
  status?: TemaStatus;
}

export interface Modulo {
  id: string;
  title: string;
  description: string;
  duration: string;
  temas: Tema[];
}

export interface Curso {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  duration: string;
  ageMin: number;
  ageMax: number;
  progress: number;
  cover: string;
  modulos: Modulo[];
}

export interface Pregunta {
  id: string;
  enunciado: string;
  opciones: string[];
  correcta: number;
}

// ===== API Types =====
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  message: string;
  statusCode: number;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}
