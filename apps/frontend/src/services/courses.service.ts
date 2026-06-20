import { api } from './api';
import type { Curso, Pregunta } from '@/types';
import { cursos as mockCursos, preguntasMock } from '@/lib/mock';

/**
 * Courses service - abstracción sobre las llamadas API de cursos.
 * Actualmente devuelve datos mock. Cuando el backend esté listo,
 * descomentar las llamadas reales y eliminar los mocks.
 */
export const coursesService = {
  async getAll(): Promise<Curso[]> {
    // TODO: Conectar con backend real
    // return api.get<Curso[]>('/courses');
    return mockCursos;
  },

  async getById(id: string): Promise<Curso | undefined> {
    // TODO: Conectar con backend real
    // return api.get<Curso>(`/courses/${id}`);
    return mockCursos.find(c => c.id === id);
  },

  async getPreguntas(cursoId: string, temaId: string): Promise<Pregunta[]> {
    // TODO: Conectar con backend real
    // return api.get<Pregunta[]>(`/courses/${cursoId}/temas/${temaId}/preguntas`);
    return preguntasMock;
  },

  async submitExam(cursoId: string, temaId: string, respuestas: number[]): Promise<{ score: number; aprobado: boolean }> {
    // TODO: Conectar con backend real
    // return api.post(`/courses/${cursoId}/temas/${temaId}/exam`, { respuestas });
    return { score: 80, aprobado: true };
  },
};
