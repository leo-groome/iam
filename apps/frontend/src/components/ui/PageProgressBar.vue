<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const visible = ref(false);
const width = ref(0);
let ticker: ReturnType<typeof setInterval> | null = null;
let hideTimer: ReturnType<typeof setTimeout> | null = null;

function start() {
  if (ticker) clearInterval(ticker);
  if (hideTimer) clearTimeout(hideTimer);
  width.value = 0;
  visible.value = true;
  // Exponential approach: gets to ~80% quickly then slows down (never reaches 90%)
  ticker = setInterval(() => {
    width.value += (88 - width.value) * 0.08;
  }, 80);
}

function done() {
  if (ticker) { clearInterval(ticker); ticker = null; }
  width.value = 100;
  hideTimer = setTimeout(() => {
    visible.value = false;
    width.value = 0;
  }, 350);
}

const router = useRouter();
router.beforeEach(() => start());
router.afterEach(() => done());
</script>

<template>
  <Transition name="bar-fade">
    <div
      v-if="visible"
      class="fixed top-0 left-0 right-0 z-[9999] pointer-events-none"
      style="height: 2px;"
    >
      <div
        class="h-full bg-[var(--color-primary)] transition-[width] duration-150 ease-out"
        :style="{ width: width + '%' }"
      ></div>
    </div>
  </Transition>
</template>

<style scoped>
.bar-fade-leave-active {
  transition: opacity 0.3s ease 0.05s;
}
.bar-fade-leave-to {
  opacity: 0;
}
</style>
