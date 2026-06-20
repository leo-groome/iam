export type Tema = {
  id: string;
  title: string;
  type: 'video' | 'pdf' | 'imagen' | 'texto';
  duration: string;
  hasExam: boolean;
  status?: 'bloqueado' | 'disponible' | 'aprobado' | 'en_repaso';
};

export type Modulo = {
  id: string;
  title: string;
  description: string;
  duration: string;
  temas: Tema[];
};

export type Curso = {
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
};

export const cursos: Curso[] = [
  {
    id: 'acompanamiento-social',
    title: 'Acompañamiento social y defensa de la vida',
    subtitle: 'Curso disponible',
    description: 'Aprende a mirar, escuchar y orientar a quienes lo necesitan. Un recorrido humano para canalizar apoyo con respeto.',
    duration: '45 min',
    ageMin: 18,
    ageMax: 99,
    progress: 25,
    cover: '/covers/acompanamiento-social.jpg',
    modulos: [
      {
        id: 'm1',
        title: 'Modulo 1: Mirar, escuchar y orientar',
        description: 'Una clase breve con enfoque humano: como reconocer necesidades, comunicar apoyo y canalizar recursos con respeto.',
        duration: '12 min',
        temas: [
          { id: 't1', title: 'Mirar con atención', type: 'video', duration: '5 min', hasExam: true, status: 'aprobado' },
          { id: 't2', title: 'Escuchar con respeto', type: 'video', duration: '4 min', hasExam: true, status: 'disponible' },
          { id: 't3', title: 'Orientar con claridad', type: 'video', duration: '3 min', hasExam: true, status: 'bloqueado' },
        ],
      },
      {
        id: 'm2',
        title: 'Modulo 2: Recursos y red de apoyo',
        description: 'Conoce a quién acudir y cómo conectar a las personas con los servicios adecuados.',
        duration: '15 min',
        temas: [
          { id: 't4', title: 'Mapa de recursos locales', type: 'pdf', duration: '6 min', hasExam: true, status: 'bloqueado' },
          { id: 't5', title: 'Protocolo de canalización', type: 'video', duration: '9 min', hasExam: true, status: 'bloqueado' },
        ],
      },
      {
        id: 'm3',
        title: 'Modulo 3: Cuidado de quien acompaña',
        description: 'Tu bienestar también importa. Estrategias de autocuidado para acompañantes.',
        duration: '18 min',
        temas: [
          { id: 't6', title: 'Reconocer mis límites', type: 'texto', duration: '8 min', hasExam: false, status: 'bloqueado' },
          { id: 't7', title: 'Buscar apoyo', type: 'video', duration: '10 min', hasExam: true, status: 'bloqueado' },
        ],
      },
    ],
  },
  {
    id: 'primeros-auxilios-emocionales',
    title: 'Primeros auxilios emocionales',
    subtitle: 'Curso disponible',
    description: 'Herramientas prácticas para apoyar a alguien en una crisis emocional momentánea.',
    duration: '30 min',
    ageMin: 18,
    ageMax: 99,
    progress: 0,
    cover: '/covers/primeros-auxilios-emocionales.jpg',
    modulos: [
      {
        id: 'm1',
        title: 'Modulo 1: Reconocer la crisis',
        description: 'Identifica señales tempranas de una crisis emocional.',
        duration: '15 min',
        temas: [
          { id: 't1', title: 'Señales emocionales', type: 'video', duration: '7 min', hasExam: true, status: 'disponible' },
          { id: 't2', title: 'Señales físicas', type: 'video', duration: '8 min', hasExam: true, status: 'bloqueado' },
        ],
      },
      {
        id: 'm2',
        title: 'Modulo 2: Respuesta inmediata',
        description: 'Qué hacer en los primeros minutos.',
        duration: '15 min',
        temas: [
          { id: 't3', title: 'Contención básica', type: 'video', duration: '8 min', hasExam: true, status: 'bloqueado' },
          { id: 't4', title: 'Cuándo llamar a un profesional', type: 'texto', duration: '7 min', hasExam: true, status: 'bloqueado' },
        ],
      },
    ],
  },
  {
    id: 'comunicacion-empatica',
    title: 'Comunicación empática',
    subtitle: 'Curso disponible',
    description: 'Mejora tus habilidades para comunicarte con personas en situación vulnerable.',
    duration: '40 min',
    ageMin: 18,
    ageMax: 99,
    progress: 100,
    cover: '/covers/comunicacion-empatica.jpg',
    modulos: [
      {
        id: 'm1',
        title: 'Modulo 1: Bases de la empatía',
        description: 'Qué es y qué no es ser empático.',
        duration: '20 min',
        temas: [
          { id: 't1', title: 'Definir empatía', type: 'video', duration: '10 min', hasExam: true, status: 'aprobado' },
          { id: 't2', title: 'Errores comunes', type: 'video', duration: '10 min', hasExam: true, status: 'aprobado' },
        ],
      },
    ],
  },
];

export const preguntasMock = [
  {
    id: 'q1',
    enunciado: '¿Cuál es el primer paso al acompañar a alguien?',
    opciones: ['Resolver su problema', 'Escuchar sin juzgar', 'Dar consejos rápidos', 'Recomendar un profesional'],
    correcta: 1,
  },
  {
    id: 'q2',
    enunciado: '¿Qué actitud refleja mejor el respeto a la persona?',
    opciones: ['Interrumpir para corregir', 'Hacer preguntas con curiosidad genuina', 'Asumir lo que necesita', 'Resolver por ella'],
    correcta: 1,
  },
  {
    id: 'q3',
    enunciado: '¿Cuándo conviene canalizar a un servicio especializado?',
    opciones: ['Siempre', 'Cuando la situación rebasa tu capacidad de apoyo', 'Solo si la persona lo pide', 'Nunca'],
    correcta: 1,
  },
];

export function findCurso(id: string) {
  return cursos.find(c => c.id === id);
}
