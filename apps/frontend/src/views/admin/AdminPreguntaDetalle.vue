<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { onMounted, ref, computed } from 'vue';
import { adminService } from '@/services/admin.service';
import { apiGet } from '@/lib/api';
import RichTextEditor from '@/components/ui/RichTextEditor.vue';

const route = useRoute();
const router = useRouter();
const courseId = route.params.id as string;
const modId = route.params.modId as string;
const temaId = route.params.temaId as string;
const qId = route.params.qId as string;

// Determine scope: if route has modId but no temaId, it's module-scope
const isModuleScope = computed(() => !!modId && !temaId);

const isNew = qId === 'nueva';
const pregunta = ref(null);
const loading = ref(false);
const enunciado = ref('');
const opts = ref<string[]>(['', '', '']);
const correctIdx = ref(0);

onMounted(async () => {
  if (!isNew) {
    loading.value = true;
    try {
      const q = await (apiGet as any)('/api/v1/admin/questions/' + qId);
      pregunta.value = q;
      enunciado.value = q.enunciado;
      opts.value = q.options.map((o: any) => o.texto);
      correctIdx.value = q.options.findIndex((o: any) => o.is_correct);
    } catch (err) {
      console.error('Error loading question:', err);
    } finally {
      loading.value = false;
    }
  }
});

const addOption = () => {
  if (opts.value.length < 5) {
    opts.value.push('');
  }
};

const removeOption = (i: number) => {
  if (opts.value.length > 3) {
    opts.value.splice(i, 1);
    if (correctIdx.value >= opts.value.length) {
      correctIdx.value = opts.value.length - 1;
    }
  }
};

const handleSave = async () => {
  try {
    if (isNew) {
      if (isModuleScope.value) {
        await adminService.createModuleQuestion(modId, {
          enunciado: enunciado.value,
          options: opts.value.map((t, i) => ({
            texto: t,
            is_correct: i === correctIdx.value
          }))
        });
      } else {
        await adminService.createQuestion(temaId, {
          enunciado: enunciado.value,
          options: opts.value.map((t, i) => ({
            texto: t,
            is_correct: i === correctIdx.value
          }))
        });
      }
    } else {
      await adminService.updateQuestion(qId, enunciado.value);
      for (let i = 0; i < opts.value.length; i++) {
        const option = (pregunta.value as any)?.options[i];
        if (option) {
          await adminService.updateOption(option.id, {
            texto: opts.value[i],
            is_correct: i === correctIdx.value
          });
        }
      }
    }
    router.push(backUrl.value);
  } catch (err) {
    console.error('Error saving question:', err);
  }
};

const backUrl = computed(() => {
  if (isModuleScope.value) {
    return `/admin/cursos/${courseId}/modulos/${modId}`;
  }
  return `/admin/cursos/${courseId}/modulos/${modId}/temas/${temaId}/preguntas`;
});

const backLabel = computed(() => isModuleScope.value ? '← Módulo' : '← Banco de preguntas');
const pageTitle = computed(() => {
  if (isNew) return isModuleScope.value ? 'Nueva pregunta diagnóstica' : 'Nueva pregunta';
  return isModuleScope.value ? 'Editar pregunta diagnóstica' : 'Editar pregunta';
});
</script>

<template>
  <div class="page-container">


  <router-link :to="backUrl" class="text-sm text-[var(--color-text-muted)] mb-3 inline-block">{{ backLabel }}</router-link>
  <header class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold">{{ pageTitle }}</h1>
    <div class="flex gap-2">
      <router-link :to="backUrl" class="btn btn-secondary">Cancelar</router-link>
      <button @click="handleSave" class="btn btn-primary">Guardar</button>
    </div>
  </header>

  <div class="card p-6 space-y-5 max-w-2xl">
    <div>
      <label class="label">Enunciado</label>
      <RichTextEditor v-model="enunciado" placeholder="Escribe la pregunta" />
      <p class="help">5–300 caracteres.</p>
    </div>
    <div>
      <label class="label">Opciones de respuesta</label>
      <p class="help mb-3">Marca cuál es la correcta (3 a 5 opciones).</p>
      <div class="space-y-2">
        <div v-for="(opt, i) in opts" :key="i" class="flex items-center gap-3">
          <input type="radio" name="correcta" :checked="i === correctIdx" @change="correctIdx = i" class="w-5 h-5 accent-[var(--color-primary)]" />
          <input class="input flex-1" maxlength="150" v-model="opts[i]" :placeholder="`Opción ${i + 1}`" />
          <button type="button" @click="removeOption(i)" class="text-[var(--color-text-muted)] hover:text-[var(--color-error)]" aria-label="Eliminar">✕</button>
        </div>
      </div>
      <button type="button" @click="addOption" class="btn btn-ghost mt-3 text-sm">+ Agregar opción</button>
    </div>
  </div>


  </div>
</template>
