<script setup lang="ts" generic="T extends string">
import { useId } from 'vue'

import { INPUT_CLASS } from './styles'

const model = defineModel<T | ''>({ required: true })

withDefaults(
  defineProps<{
    label: string
    options: readonly { value: T; title: string }[]
    /** Подпись пустого варианта. Нет — пустого варианта в списке нет. */
    placeholder?: string
    hint?: string
    disabled?: boolean
  }>(),
  { placeholder: undefined, hint: '', disabled: false },
)

const id = useId()
</script>

<template>
  <div class="flex min-w-0 flex-col gap-1">
    <label :for="id" class="font-label-md text-label-md text-on-surface">{{ label }}</label>
    <select :id="id" v-model="model" :disabled="disabled" :class="INPUT_CLASS">
      <option v-if="placeholder !== undefined" value="" disabled>{{ placeholder }}</option>
      <option v-for="option in options" :key="option.value" :value="option.value">{{ option.title }}</option>
    </select>
    <span v-if="hint" class="font-body-sm text-body-sm text-outline">{{ hint }}</span>
  </div>
</template>
