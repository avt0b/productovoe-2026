<script setup lang="ts">
import { computed, ref, watch } from 'vue'

/**
 * Аватар любого человека (краевед, автор отзыва). Нет ссылки или картинка не
 * загрузилась — кружок с первой буквой имени. `UserAvatar` из ui/ показывает
 * только текущего пользователя, поэтому чужим нужен свой.
 */
const props = withDefaults(defineProps<{ name: string; url: string | null; size?: number }>(), { size: 40 })

const failed = ref(false)
watch(() => props.url, () => (failed.value = false))

const showImage = computed(() => !!props.url && !failed.value)
const letter = computed(() => props.name.trim().charAt(0).toUpperCase() || '?')
const box = computed(() => ({ width: `${props.size}px`, height: `${props.size}px` }))
</script>

<template>
  <img
    v-if="showImage"
    :src="url ?? undefined"
    :alt="name"
    :style="box"
    class="shrink-0 rounded-full object-cover"
    @error="failed = true"
  />
  <span
    v-else
    :style="box"
    class="flex shrink-0 items-center justify-center rounded-full bg-secondary-container font-headline-sm text-headline-sm text-on-secondary-container"
    aria-hidden="true"
  >
    {{ letter }}
  </span>
</template>
