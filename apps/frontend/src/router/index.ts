import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: Array<RouteRecordRaw> = [
  // Públicas
  {
    path: '/',
    redirect: () => {
      const store = useAuthStore()
      if (store.isAuthenticated) return '/catalogo'
      return localStorage.getItem('hasCompletedOnboarding') ? '/login' : '/onboarding'
    }
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/views/public/OnboardingView.vue'),
    meta: { layout: 'PublicLayout' },
    beforeEnter: (to, from, next) => {
      const store = useAuthStore()
      if (store.isAuthenticated) {
        next('/catalogo')
      } else if (localStorage.getItem('hasCompletedOnboarding')) {
        next('/login')
      } else {
        next()
      }
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/public/login.vue'),
    meta: { layout: 'PublicLayout' }
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('@/views/public/signup.vue'),
    meta: { layout: 'PublicLayout' }
  },
  {
    path: '/recuperar-contrasena',
    name: 'RecuperarContrasena',
    component: () => import('@/views/public/recuperar-contrasena.vue'),
    meta: { layout: 'PublicLayout' }
  },
  {
    path: '/restablecer-contrasena',
    name: 'RestablecerContrasena',
    component: () => import('@/views/public/restablecer-contrasena.vue'),
    meta: { layout: 'PublicLayout' }
  },
  // Compat: rutas legacy redirigen a /login y /signup
  { path: '/registro', redirect: (to) => ({ path: '/signup', query: to.query }) },
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

  // Panel de Estudiante
  {
    path: '/diagnostico',
    name: 'Diagnostico',
    component: () => import('@/views/student/DiagnosticoView.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/catalogo',
    name: 'Catalogo',
    component: () => import('@/views/public/catalogo.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/perfil',
    name: 'Perfil',
    component: () => import('@/views/public/perfil.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:slug',
    name: 'CourseDashboard',
    component: () => import('@/views/student/CourseDashboard.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:slug/tema/:topicId',
    name: 'LessonView',
    component: () => import('@/views/student/LessonView.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:slug/tema/:topicId/examen',
    name: 'ExamView',
    component: () => import('@/views/student/ExamView.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:slug/tema/:topicId/resultado',
    name: 'ExamResult',
    component: () => import('@/views/student/ExamResult.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:slug/progreso',
    name: 'CourseProgress',
    component: () => import('@/views/student/CourseProgress.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },
  {
    path: '/curso/:slug/certificado',
    name: 'CourseCertificate',
    component: () => import('@/views/student/CourseCertificate.vue'),
    meta: { layout: 'StudentLayout', requiresAuth: true }
  },

  // Panel Admin
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/AdminDashboard.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true, keepAlive: true }
  },
  {
    path: '/admin/cursos',
    name: 'AdminCursos',
    component: () => import('@/views/admin/AdminCursos.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true, keepAlive: true }
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
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true, keepAlive: true }
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
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true, keepAlive: true }
  },
  {
    path: '/admin/configuracion',
    name: 'AdminConfiguracion',
    component: () => import('@/views/admin/AdminConfiguracion.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true }
  },
  // Admin Landing Control
  {
    path: '/admin/landing',
    name: 'AdminLanding',
    component: () => import('@/views/admin/landing/AdminLanding.vue'),
    meta: { layout: 'AdminLayout', requiresAuth: true, requiresAdmin: true },
    redirect: '/admin/landing/inicio',
    children: [
      {
        path: 'inicio',
        name: 'AdminLandingInicio',
        component: () => import('@/views/admin/landing/SeccionInicio.vue')
      },
      {
        path: 'pilares',
        name: 'AdminLandingPilares',
        component: () => import('@/views/admin/landing/SeccionPilares.vue')
      },
      {
        path: 'quienes-somos',
        name: 'AdminLandingQuienesSomos',
        component: () => import('@/views/admin/landing/SeccionQuienesSomos.vue')
      },
      {
        path: 'ecos',
        name: 'AdminLandingEcos',
        component: () => import('@/views/admin/landing/EcosEditor.vue')
      }
    ]
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
  {
    path: '/admin/cursos/:id/modulos/:modId/examen-diagnostico/:qId',
    name: 'AdminPreguntaModuloDetalle',
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    return savedPosition ?? { top: 0 }
  }
})

// Auth Guards
router.beforeEach(async (to, _from, next) => {
  const store = useAuthStore()

  if (!store.initialized) {
    await store.init()
  }

  const isAuthenticated = store.isAuthenticated
  const isAdmin = store.isAdmin
  const isInstructor = store.isInstructor

  // Auth pages: redirect authenticated users away
  if ((to.path === '/login' || to.path === '/signup' || to.path === '/registro') && isAuthenticated) {
    const nextPath = (to.query.next as string) || '/catalogo'
    return next(nextPath)
  }

  // Private routes: require authentication
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next({ path: '/login', query: { next: to.fullPath } })
  }

  // Admin routes: require admin or instructor
  if (to.meta.requiresAdmin && !isAdmin && !isInstructor) {
    return next('/catalogo')
  }

  next()
})

export default router

// Vue Router meta type augmentation
declare module 'vue-router' {
  interface RouteMeta {
    layout?: 'PublicLayout' | 'StudentLayout' | 'AdminLayout'
    requiresAuth?: boolean
    requiresAdmin?: boolean
    showHeader?: boolean
    wide?: boolean
    progress?: number
    courseName?: string
    keepAlive?: boolean
  }
}
