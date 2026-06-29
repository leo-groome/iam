import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import tailwindcss from '@tailwindcss/vite';
import VueDevTools from 'vite-plugin-vue-devtools';
import path from 'path';

export default defineConfig({
  plugins: [
    vue(),
    VueDevTools(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // @ffmpeg/ffmpeg uses internal Web Workers that Vite cannot pre-bundle.
  // Excluding them prevents the "disallowed MIME type" worker error in dev.
  optimizeDeps: {
    exclude: ['@ffmpeg/ffmpeg', '@ffmpeg/util'],
  },
  server: {
    port: 4321,
    // NOTE: COOP/COEP headers were removed because they block cross-origin fetch
    // (R2 presigned PUT URLs don't return Cross-Origin-Resource-Policy).
    // ffmpeg.wasm uses single-thread core (no SharedArrayBuffer required).
  },
  build: {
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) {
              return 'vendor-vue'; // Vue y sus utilidades básicas
            }
            if (id.includes('ffmpeg')) {
              return 'vendor-ffmpeg'; // Procesamiento multimedia pesado
            }
            return 'vendor'; // El resto de dependencias (lucide, zod, tailwind, etc.)
          }
        }
      }
    }
  },
});
