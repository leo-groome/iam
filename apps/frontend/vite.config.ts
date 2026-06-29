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
    headers: {
      // Required for SharedArrayBuffer (used by ffmpeg.wasm for multi-threading)
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
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
