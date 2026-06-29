<script setup lang="ts">
import { computed } from 'vue'
import { createAvatar } from '@dicebear/core'
import { thumbs } from '@dicebear/collection'

const props = withDefaults(defineProps<{
  name?: string
  size?: string
}>(), {
  name: '?',
  size: 'w-8 h-8'
})

const avatarSvg = computed(() => {
  const avatar = createAvatar(thumbs, {
    seed: props.name || '?',
    radius: 50,
    backgroundColor: ['b6e3f4','c0aede','d1d4f9','ffd5dc','ffdfbf'],
  })
  return avatar.toString()
})
</script>

<template>
  <div :class="[size, 'shrink-0 flex items-center justify-center overflow-hidden rounded-full shadow-sm']" v-html="avatarSvg">
  </div>
</template>
