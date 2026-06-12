# PRD — Landing Page IAM (Infancia y Adolescencia Misioneras)

## 1. Resumen
Landing page de una sola página (SPA scroll) para ONG pro-vida. Objetivo: concientizar sobre el aborto, mostrar testimonios reales, invitar a involucrarse (donar / voluntariado / contacto).

## 2. Objetivos
- Transmitir mensaje pro-vida con tono empático, no agresivo.
- Maximizar impacto visual mediante imágenes grandes y espacio en blanco.
- Conversión: donación, voluntariado, suscripción newsletter.

## 3. Stack
- **Framework:** Astro 4 + TypeScript
- **Estilos:** Tailwind CSS (`@astrojs/tailwind`)
- **Interactividad:** islas Astro con vanilla JS / mínimas React islands si hace falta
- **Animaciones:** GSAP + ScrollTrigger (scroll-linked embrión), Motion One para micro-interacciones
- **Imágenes:** `astro:assets` (`<Image />`) con optimización automática
- **Deploy:** Vercel (adapter `@astrojs/vercel/static`)

## 4. Paleta (confirmada)
Extraída de Figma + logo IAM:
- `--primary`: `#1E3A8A` (azul fuerte — botones, headlines)
- `--primary-light`: `#7BA7D9` (azul celeste del logo — acentos)
- `--accent`: `#DC2626` (rojo corazón del logo — CTA secundario, énfasis)
- `--bg`: `#F5F7FB` (off-white azulado del Figma)
- `--surface`: `#FFFFFF` (cards)
- `--text`: `#0A0E1A` (negro suave)
- `--text-muted`: `#6B7280` (gris descripciones)
- `--border`: `#E5E7EB`

## 5. Estructura de secciones

### 5.1 Hero
- Headline grande + subtítulo + CTA principal (Donar)
- Fondo: **inicio de la animación del embrión** (canvas/SVG fijo detrás)
- Imagen grande lateral o full-bleed

### 5.2 Misión
- Texto corto, 2-3 frases
- Grid 3 columnas con íconos/valores
- Fondo: embrión en etapa temprana sigue visible

### 5.3 El Problema (datos)
- Estadísticas con contadores animados
- Imagen grande de contexto
- Fondo: embrión avanza etapa

### 5.4 Galería / Situaciones reales
- Grid masonry de 6-9 imágenes
- Hover: overlay con frase corta

### 5.5 Historias / Testimonios
- Carrusel o grid de cards
- Foto + nombre + testimonio
- 4-6 historias iniciales

### 5.6 Cómo Ayudar
- 3 cards: Donar / Voluntariado / Compartir
- Fondo: embrión convertido en bebé (final de animación)

### 5.7 Contacto / Newsletter
- Form simple (nombre, email, mensaje)
- Links a redes sociales

### 5.8 Footer
- Logo, links, copyright, redes

## 6. Animación embrión → bebé (clave)
- **Implementación:** SVG morphing o secuencia de PNGs (15-20 frames) controlada con `ScrollTrigger`
- **Posición:** `position: fixed`, lado derecho o centro con baja opacidad (15-25%) para no competir con contenido
- **Activo durante:** secciones 5.1 → 5.6
- **Fallback:** si el dispositivo es móvil pequeño o `prefers-reduced-motion`, mostrar imagen estática
- **Performance:** lazy-load frames, usar `will-change: transform`, throttle scroll

## 7. Slots de imágenes (placeholders necesarios)
- Hero: 1 imagen grande (1920x1080)
- Misión: 3 íconos
- Problema: 1 imagen contexto (1200x800)
- Galería: 9 imágenes (800x800 cada una)
- Historias: 6 retratos (400x400)
- Frames embrión: 15-20 PNGs (transparente, 800x800)
- Logo ONG: SVG

## 8. Responsive
- Mobile-first
- Breakpoints Tailwind default (sm/md/lg/xl)
- Animación embrión simplificada en mobile (3-4 frames, no scroll-linked)

## 9. Accesibilidad
- WCAG AA contraste
- Alt text en todas las imágenes
- `prefers-reduced-motion` respetado
- Form con labels y aria
- Navegación por teclado

## 10. SEO
- Meta tags + Open Graph
- `sitemap.xml`, `robots.txt`
- Structured data (Organization schema)
- Optimización Core Web Vitals

## 11. Entregables / Orden de ejecución
1. Setup Astro + Tailwind + estructura carpetas (`src/pages/index.astro`, `src/components/`, `src/layouts/`)
2. Variables CSS de paleta (placeholders hasta confirmar Figma)
3. Layout base + footer + header
4. Hero + Misión (estáticos)
5. Problema + Galería + Historias
6. Cómo Ayudar + Contacto
7. Animación embrión (último, sobre base estable)
8. Responsive QA + accesibilidad
9. Deploy Vercel

## 12. Pendientes / Decisiones del usuario
- [x] Colores — confirmados
- [x] Logo — IAM (provisto)
- [x] Nombre — Infancia y Adolescencia Misioneras
- [x] Imágenes — stock (Unsplash/Pexels) en v1
- [ ] Copy real (textos, headlines, testimonios) — se usará placeholder coherente con tono católico/pro-vida
- [ ] Endpoint para form — placeholder, conectar después
- [ ] Pasarela de donación — placeholder link externo

## 13. Fuera de alcance v1
- CMS / panel admin
- Multi-idioma
- Blog
- Cuenta de usuario
