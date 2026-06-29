<template>
  <div class="relative w-full min-h-screen bg-[var(--color-app-bg)] text-[var(--color-text)] flex flex-col items-center justify-center overflow-hidden">
    
    <Transition name="fade-slow">
      <!-- Splash Screen -->
      <div v-if="showSplash" class="absolute inset-0 z-50 flex flex-col items-center justify-center bg-[var(--color-app-bg)]">
        <img loading="lazy" src="/MISIONERAS_LOGO.svg" alt="IAM de la Vida" class="w-64 md:w-80 lg:w-96 h-auto drop-shadow-xl animate-pulse" />
      </div>
    </Transition>

    <!-- Main Content -->
    <div v-show="!showSplash" class="absolute inset-0 w-full h-full flex flex-col items-center">
      
      <!-- Top Bar / Logo -->
      <header class="w-full p-6 flex flex-col items-center justify-center relative z-20">
        <div class="flex items-center gap-3 opacity-80">
          <img loading="lazy" src="/MISIONERAS_LOGO.svg" alt="Logo" class="w-8 h-auto" />
          <span class="font-display font-semibold tracking-wider text-[var(--color-primary)] uppercase text-sm">IAM de la Vida</span>
        </div>
      </header>

      <!-- Global Progress Bar -->
      <div class="absolute top-0 left-0 w-full h-1 bg-[var(--color-border)] z-30">
        <div 
          class="h-full bg-[var(--color-primary)] transition-all duration-700 ease-out"
          :style="{ width: `${progressPercentage}%` }"
        ></div>
      </div>

      <!-- Cards Container -->
      <div class="flex-1 w-full flex items-center justify-center px-4 relative z-10 perspective-1000">
        
        <div class="relative w-full max-w-lg h-[550px]">
          
          <div
            v-for="(step, index) in steps"
            :key="step.id"
            class="absolute top-0 left-0 w-full h-full bg-[var(--color-surface)] rounded-3xl p-6 md:p-10 shadow-2xl border border-[var(--color-border)] transition-all duration-500 ease-out flex flex-col overflow-hidden"
            :style="getCardStyle(index)"
            :class="getCardClass(index)"
          >
            
            <!-- Card Header -->
            <div class="mb-4 flex justify-between items-center shrink-0">
              <span class="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">
                Pregunta {{ index + 1 }} de {{ steps.length }}
              </span>
              <button 
                v-if="index === currentStep && currentStep > 0" 
                @click.stop="prevStep"
                class="w-8 h-8 rounded-full bg-[var(--color-app-bg)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors border border-[var(--color-border)]"
                title="Volver"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            </div>
            
            <h2 class="text-2xl md:text-3xl font-bold mb-6 leading-snug font-display text-center shrink-0">
              {{ step.question }}
            </h2>

            <!-- Input Types -->
            <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4 flex flex-col justify-end">
              
              <!-- TYPE: OPTIONS -->
              <div v-if="step.type === 'options'" class="space-y-3 mt-auto">
                <button
                  v-for="(option, optIndex) in step.options"
                  :key="optIndex"
                  @click="selectOption(option.value)"
                  :disabled="index !== currentStep"
                  class="w-full text-left px-6 py-4 rounded-full border-2 transition-all duration-300 group flex items-center justify-between"
                  :class="
                    answers[step.id] === option.value
                      ? 'border-[var(--color-primary)] bg-[var(--color-primary)] text-white shadow-lg transform scale-[1.02]'
                      : 'border-[var(--color-border)] bg-transparent hover:border-[var(--color-primary)] hover:bg-[var(--color-app-bg)]'
                  "
                >
                  <span class="text-base md:text-lg font-medium" :class="answers[step.id] === option.value ? 'text-white' : ''">
                    {{ option.label }}
                  </span>
                  
                  <div 
                    class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-300 shrink-0 ml-4"
                    :class="answers[step.id] === option.value ? 'border-white bg-transparent' : 'border-gray-300 group-hover:border-[var(--color-primary)]'"
                  >
                    <svg v-if="answers[step.id] === option.value" xmlns="http://www.w3.org/2000/svg" class="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </button>
              </div>

              <!-- TYPE: TEXT -->
              <div v-else-if="step.type === 'text'" class="mt-auto space-y-6">
                <div class="space-y-2">
                  <input
                    v-model="textInputState"
                    type="text"
                    :placeholder="step.placeholder"
                    :disabled="index !== currentStep"
                    class="w-full px-6 py-4 text-lg rounded-full border-2 bg-transparent focus:outline-none transition-colors"
                    :class="textInputError && index === currentStep
                      ? 'border-red-400 focus:border-red-500'
                      : 'border-[var(--color-border)] focus:border-[var(--color-primary)]'"
                    @keydown.enter="submitText"
                    @input="textInputError = ''"
                  />
                  <p
                    v-if="textInputError && index === currentStep"
                    class="text-red-500 text-sm px-4"
                  >{{ textInputError }}</p>
                </div>
                <button
                  @click="submitText"
                  :disabled="!textInputState.trim() || index !== currentStep"
                  class="w-full py-4 rounded-full font-bold text-white transition-all"
                  :class="textInputState.trim() ? 'bg-[var(--color-primary)] hover:opacity-90 hover:shadow-lg transform hover:scale-[1.02]' : 'bg-gray-300 cursor-not-allowed'"
                >
                  Continuar
                </button>
              </div>

              <!-- TYPE: SEARCHABLE SELECT -->
              <div v-else-if="step.type === 'searchable_select'" class="flex flex-col h-full mt-2">
                <div class="relative mb-4 shrink-0">
                  <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="Buscar..."
                    :disabled="index !== currentStep"
                    class="w-full pl-11 pr-4 py-3 rounded-full border-2 border-[var(--color-border)] bg-[var(--color-app-bg)] focus:border-[var(--color-primary)] focus:outline-none transition-colors"
                  />
                </div>
                
                <div class="flex-1 overflow-y-auto custom-scrollbar space-y-2 pr-2">
                  <button
                    v-for="(item, itemIndex) in filteredList(step.searchList || [])"
                    :key="itemIndex"
                    @click="selectOption(item)"
                    :disabled="index !== currentStep"
                    class="w-full text-left px-5 py-3 rounded-xl border transition-all duration-200 group flex items-center justify-between"
                    :class="
                      answers[step.id] === item
                        ? 'border-[var(--color-primary)] bg-[var(--color-primary-soft)] text-[var(--color-primary)] font-semibold'
                        : 'border-transparent bg-[var(--color-app-bg)] hover:border-[var(--color-primary)]'
                    "
                  >
                    <span class="text-sm md:text-base truncate">{{ item }}</span>
                  </button>
                  <p v-if="filteredList(step.searchList || []).length === 0" class="text-center text-sm text-[var(--color-text-muted)] py-4">
                    No se encontraron resultados
                  </p>
                </div>
              </div>

            </div>

          </div>

        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { diocesisMexico, parroquiasCancunChetumal, ciudadesMexico } from '@/data/onboardingData';

const router = useRouter();
const showSplash = ref(true);

onMounted(() => {
  setTimeout(() => {
    showSplash.value = false;
  }, 2000);
});

type StepType = 'options' | 'text' | 'searchable_select';

interface Step {
  id: string;
  question: string;
  type: StepType;
  options?: { label: string; value: string }[];
  placeholder?: string;
  searchList?: string[];
}

const steps: Step[] = [
  {
    id: 'nombre',
    question: '¿Cuál es tu nombre completo?',
    type: 'text',
    placeholder: 'Escribe tu nombre y apellidos'
  },
  {
    id: 'edad',
    question: '¿Qué edad tienes?',
    type: 'options',
    options: [
      { label: 'Menos de 18 años', value: '<18' },
      { label: '18 a 25 años', value: '18-25' },
      { label: '26 a 35 años', value: '26-35' },
      { label: '36 a 50 años', value: '36-50' },
      { label: 'Más de 50 años', value: '>50' }
    ]
  },
  {
    id: 'sexo',
    question: '¿Cuál es tu sexo?',
    type: 'options',
    options: [
      { label: 'Hombre', value: 'Hombre' },
      { label: 'Mujer', value: 'Mujer' }
    ]
  },
  {
    id: 'diocesis',
    question: '¿A qué Diócesis perteneces?',
    type: 'searchable_select',
    searchList: diocesisMexico
  },
  {
    id: 'ciudad',
    question: '¿De qué ciudad nos visitas?',
    type: 'searchable_select',
    searchList: ciudadesMexico
  },
  {
    id: 'parroquia',
    question: '¿Cuál es tu parroquia?',
    type: 'searchable_select',
    searchList: parroquiasCancunChetumal
  },
  {
    id: 'entorno',
    question: '¿Tu parroquia está en zona rural o urbana?',
    type: 'options',
    options: [
      { label: 'Rural', value: 'Rural' },
      { label: 'Urbana', value: 'Urbana' }
    ]
  },
  {
    id: 'pastoral',
    question: '¿En qué área de pastoral sirves?',
    type: 'options',
    options: [
      { label: 'Infancia y Adolescencia Misionera (IAM)', value: 'IAM' },
      { label: 'Catequesis', value: 'Catequesis' },
      { label: 'Pastoral Juvenil', value: 'Juvenil' },
      { label: 'Pastoral Familiar', value: 'Familiar' },
      { label: 'Otra', value: 'Otra' }
    ]
  }
];

const currentStep = ref(0);
const answers = ref<Record<string, string>>({});
const textInputState = ref('');
const textInputError = ref('');
const searchQuery = ref('');

const FULL_NAME_RE = /^[A-Za-zÀ-ÖØ-öø-ÿ\u00C0-\u024F\s]+$/

// Reset temporary states when step changes
watch(currentStep, (newStep) => {
  searchQuery.value = '';
  textInputError.value = '';
  
  const currentId = steps[newStep].id;
  if (answers.value[currentId] && steps[newStep].type === 'text') {
    textInputState.value = answers.value[currentId];
  } else {
    textInputState.value = '';
  }
});

const progressPercentage = computed(() => {
  return (currentStep.value / steps.length) * 100;
});

const filteredList = (list: string[]) => {
  if (!searchQuery.value.trim()) return list;
  const q = searchQuery.value.toLowerCase().trim();
  return list.filter(item => item.toLowerCase().includes(q));
};

const getCardStyle = (index: number) => {
  const offset = index - currentStep.value;
  
  if (offset < 0) {
    return { zIndex: 10 };
  }
  if (offset === 0) {
    return { zIndex: 50, transform: 'translateY(0) scale(1)', opacity: 1 };
  }
  if (offset === 1) {
    return { zIndex: 40, transform: 'translateY(24px) scale(0.95)', opacity: 0.8 };
  }
  if (offset === 2) {
    return { zIndex: 30, transform: 'translateY(48px) scale(0.90)', opacity: 0.5 };
  }
  
  return {
    zIndex: 20,
    transform: 'translateY(72px) scale(0.85)',
    opacity: 0,
    pointerEvents: 'none'
  };
};

const getCardClass = (index: number) => {
  const offset = index - currentStep.value;
  if (offset < 0) {
    if (index % 2 === 0) {
      return 'opacity-0 -translate-x-[120%] -rotate-6 pointer-events-none';
    } else {
      return 'opacity-0 translate-x-[120%] rotate-6 pointer-events-none';
    }
  }
  if (offset > 0) return 'pointer-events-none';
  return '';
};

const selectOption = (value: string) => {
  const currentStepData = steps[currentStep.value];
  if (answers.value[currentStepData.id] === value) return;
  
  answers.value[currentStepData.id] = value;
  advanceStep();
};

const submitText = () => {
  textInputError.value = '';
  const value = textInputState.value.trim();
  if (!value) return;

  // Validate nombre: only letters and spaces (mirrors backend constraint)
  if (steps[currentStep.value].id === 'nombre') {
    if (value.length < 3) {
      textInputError.value = 'El nombre debe tener al menos 3 caracteres'
      return
    }
    if (value.length > 80) {
      textInputError.value = 'El nombre es demasiado largo'
      return
    }
    if (!FULL_NAME_RE.test(value)) {
      textInputError.value = 'El nombre solo puede contener letras y espacios'
      return
    }
  }

  answers.value[steps[currentStep.value].id] = value;
  advanceStep();
};

const advanceStep = () => {
  setTimeout(() => {
    if (currentStep.value < steps.length - 1) {
      currentStep.value++;
    } else {
      finishOnboarding();
    }
  }, 450);
};

const prevStep = () => {
  if (currentStep.value > 0) {
    const currentId = steps[currentStep.value].id;
    if (answers.value[currentId]) delete answers.value[currentId];
    
    const prevId = steps[currentStep.value - 1].id;
    if (answers.value[prevId]) delete answers.value[prevId];
    
    currentStep.value--;
  }
};

const finishOnboarding = () => {
  sessionStorage.setItem('onboardingData', JSON.stringify(answers.value));
  localStorage.setItem('hasCompletedOnboarding', 'true');
  
  // Forward oauth query param if present
  const oauth = new URLSearchParams(window.location.search).get('oauth');
  if (oauth) {
    router.push(`/signup?oauth=${oauth}`);
  } else {
    router.push('/signup');
  }
};
</script>

<style scoped>
.fade-slow-enter-active,
.fade-slow-leave-active {
  transition: opacity 1s ease;
}
.fade-slow-enter-from,
.fade-slow-leave-to {
  opacity: 0;
}

.perspective-1000 {
  perspective: 1000px;
}

/* Custom scrollbar for searchable list */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent; 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: var(--color-border); 
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary-light); 
}
</style>
