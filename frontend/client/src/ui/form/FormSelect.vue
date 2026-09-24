<script setup lang="ts" generic="T extends string">
import { useId } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import { FIELD_HINT_CLASS, FIELD_LABEL_CLASS, FIELD_LINE_CLASS, INPUT_CLASS } from './styles'

const model = defineModel<T | ''>({ required: true })

withDefaults(
  defineProps<{
    label: string
    /** Иконка Material Symbols слева в строке. */
    icon?: string
    options: readonly { value: T; title: string }[]
    /** Подпись пустого варианта. Нет — пустого варианта в списке нет. */
    placeholder?: string
    hint?: string
    disabled?: boolean
  }>(),
  { icon: undefined, placeholder: undefined, hint: '', disabled: false },
)

const id = useId()
</script>

<template>
  <div class="flex min-w-0 flex-col space-y-space-xs">
    <label :for="id" :class="FIELD_LABEL_CLASS">{{ label }}</label>
    <div :class="FIELD_LINE_CLASS">
      <MsIcon v-if="icon" :name="icon" :size="18" class="shrink-0 text-on-surface-variant" />
      <!-- `appearance-none`: своя стрелка справа, системная в строке без рамки выглядит чужой. -->
      <select :id="id" v-model="model" :disabled="disabled" :class="[INPUT_CLASS, 'appearance-none']">
        <option v-if="placeholder !== undefined" value="" disabled>{{ placeholder }}</option>
        <option v-for="option in options" :key="option.value" :value="option.value">{{ option.title }}</option>
      </select>
      <MsIcon name="expand_more" :size="18" class="pointer-events-none shrink-0 text-on-surface-variant" />
    </div>
    <span v-if="hint" :class="FIELD_HINT_CLASS">{{ hint }}</span>
  </div>
</template>
