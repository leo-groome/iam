# Frontend — Plataforma de Formación

Stack: **Astro 5 + Vue 3 + Tailwind v4 + TypeScript**.

## Comandos

```bash
pnpm install
pnpm dev      # http://localhost:4321
pnpm build
pnpm preview
```

## Estructura

```
src/
├── pages/         # Rutas Astro (estudiante + /admin/*)
├── layouts/       # PublicLayout, StudentLayout, AdminLayout
├── components/    # Astro estáticos
│   └── ui/        # Componentes Vue interactivos
├── composables/   # Lógica Vue reutilizable
├── stores/        # Pinia + Nanostores
├── lib/           # Helpers, validaciones Zod
└── styles/        # global.css (tokens Tailwind)
```

Ver el [PRD](../../docs/PRD-Frontend.md) para reglas y límites.
