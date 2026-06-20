import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';

const routes: Array<RouteRecordRaw> = [
  // Públicas
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/public/index.vue'),
    meta: { layout: 'PublicLayout' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/admin/AdminLogin.vue'),
    meta: { layout: 'PublicLayout' }
  },
  {
    path: '/registro',
    name: 'Registro',
    component: () => import('@/views/public/registro.vue'),
    meta: { layout: 'PublicLayout' }
  },
  {
    path: '/catalogo',
    name: 'Catalogo',
    component: () => import('@/views/public/catalogo.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/terminos',
    name: 'Terminos',
    component: () => import('@/views/public/terminos.vue'),
    meta: { layout: 'PublicLayout' }
  },
  {
    path: '/privacidad',
    name: 'Privacidad',
    component: () => import('@/views/public/privacidad.vue'),
    meta: { layout: 'PublicLayout' }
  },

  // Panel de Estudiante (requiere auth idealmente)
  {
    path: '/perfil',
    name: 'Perfil',
    component: () => import('@/views/public/perfil.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:id',
    name: 'CourseDashboard',
    component: () => import('@/views/student/CourseDashboard.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:id/tema/:temaId',
    name: 'LessonView',
    component: () => import('@/views/student/LessonView.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:id/tema/:temaId/examen',
    name: 'ExamView',
    component: () => import('@/views/student/ExamView.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:id/tema/:temaId/resultado',
    name: 'ExamResult',
    component: () => import('@/views/student/ExamResult.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:id/progreso',
    name: 'CourseProgress',
    component: () => import('@/views/student/CourseProgress.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:id/certificado',
    name: 'CourseCertificate',
    component: () => import('@/views/student/CourseCertificate.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },

  // Panel Admin
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/AdminDashboard.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/cursos',
    name: 'AdminCursos',
    component: () => import('@/views/admin/AdminCursos.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/cursos/:id',
    name: 'AdminCursoDetalle',
    component: () => import('@/views/admin/AdminCursoDetalle.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/estudiantes',
    name: 'AdminEstudiantes',
    component: () => import('@/views/admin/AdminEstudiantes.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/estudiantes/:id',
    name: 'AdminEstudianteDetalle',
    component: () => import('@/views/admin/AdminEstudianteDetalle.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/reportes',
    name: 'AdminReportes',
    component: () => import('@/views/admin/AdminReportes.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/configuracion',
    name: 'AdminConfiguracion',
    component: () => import('@/views/admin/AdminConfiguracion.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },

  // Admin sub-rutas (módulos, temas, preguntas)
  {
    path: '/admin/cursos/:id/modulos/:modId',
    name: 'AdminModuloDetalle',
    component: () => import('@/views/admin/AdminModuloDetalle.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/cursos/:id/modulos/:modId/temas/:temaId',
    name: 'AdminTemaDetalle',
    component: () => import('@/views/admin/AdminTemaDetalle.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/cursos/:id/modulos/:modId/temas/:temaId/preguntas',
    name: 'AdminPreguntas',
    component: () => import('@/views/admin/AdminPreguntas.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/cursos/:id/modulos/:modId/temas/:temaId/preguntas/:qId',
    name: 'AdminPreguntaDetalle',
    component: () => import('@/views/admin/AdminPreguntaDetalle.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/public/404.vue'),
    meta: { layout: 'PublicLayout' }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 };
  }
});

// Auth Guards Básicos
router.beforeEach((to, _from, next) => {
  // Aquí irá la lógica real usando pinia store:
  // import { useAuthStore } from '@/stores/auth';
  // const authStore = useAuthStore();
  // const isAuthenticated = authStore.isAuthenticated;
  // const isAdmin = authStore.isAdmin;

  const isAuthenticated = false; // Mock — reemplazar con store
  const isAdmin = false; // Mock — reemplazar con store

  // Bypass auth en desarrollo para no bloquear las vistas
  if (to.meta.requiresAuth && !isAuthenticated && import.meta.env.PROD) {
    next({ name: 'Login' });
  } else if (to.meta.requiresAdmin && !isAdmin && import.meta.env.PROD) {
    next({ name: 'Home' });
  } else {
    next();
  }
});

export default router;

// Vue Router meta type augmentation
declare module 'vue-router' {
  interface RouteMeta {
    layout?: 'PublicLayout' | 'StudentLayout' | 'AdminLayout';
    requiresAuth?: boolean;
    requiresAdmin?: boolean;
    showHeader?: boolean;
    wide?: boolean;
    progress?: number;
    courseName?: string;
  }
}
