<script setup lang="ts">
/** Переключатель из макета. Кнопка с `role="switch"`, а не спрятанный чекбокс — так его объявляют скринридеры. */
const model = defineModel<boolean>({ required: true })

defineProps<{
  /** Подпись для скринридера, если рядом нет видимого текста, связанного с переключателем. */
  label: string
}>()
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="model"
    :aria-label="label"
    class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200 ease-in-out"
    :class="model ? 'bg-secondary' : 'bg-surface-container-highest'"
    @click="model = !model"
  >
    <span
      class="my-0.5 inline-block h-5 w-5 transform rounded-full bg-surface-container-lowest shadow-md transition duration-200 ease-in-out"
      :class="model ? 'translate-x-5' : 'translate-x-0.5'"
    />
  </button>
</template>
