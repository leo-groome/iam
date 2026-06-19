import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';
import tailwindcss from '@tailwindcss/vite';
import vercel from '@astrojs/vercel';

export default defineConfig({
  // output: 'server' makes SSR default (Astro 5).
  // Pages can opt-in to pre-rendering with `export const prerender = true`.
  // Since most pages are dynamic (auth-dependent), defaulting to server is safer.
  output: 'server',
  adapter: vercel(),
  integrations: [vue()],
  vite: {
    envPrefix: ['PUBLIC_', 'VITE_'],
    plugins: [tailwindcss()],
  },
  server: { port: 4321 },
});
