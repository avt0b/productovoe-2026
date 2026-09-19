<script setup lang="ts">
import { useId } from 'vue'

import { INPUT_CLASS } from './styles'

/**
 * Поле формы с подписью.
 *
 * У `type="number"` модель — число (пустое поле — `null`), у остальных — строка.
 */
const model = defineModel<string | number | null>({ required: true })

const props = withDefaults(
  defineProps<{
    label: string
    type?: 'text' | 'email' | 'url' | 'number' | 'date' | 'datetime-local'
    placeholder?: string
    hint?: string
    required?: boolean
    maxlength?: number
    min?: number
    max?: number
    step?: number | 'any'
    inputmode?: 'text' | 'numeric' | 'decimal' | 'url' | 'email'
  }>(),
  {
    type: 'text',
    placeholder: '',
    hint: '',
    required: false,
    maxlength: undefined,
    min: undefined,
    max: undefined,
    step: undefined,
    inputmode: undefined,
  },
)

const id = useId()

function onInput(event: Event): void {
  const raw = (event.target as HTMLInputElement).value
  if (props.type !== 'number') {
    model.value = raw
    return
  }
  const parsed = raw === '' ? null : Number(raw.replace(',', '.'))
  model.value = parsed === null || Number.isFinite(parsed) ? parsed : model.value
}
</script>

<template>
  <div class="flex min-w-0 flex-col gap-1">
    <label :for="id" class="font-label-md text-label-md text-on-surface">{{ label }}</label>
    <input
      :id="id"
      :value="model ?? ''"
      :type="type"
      :placeholder="placeholder"
      :required="required"
      :maxlength="maxlength"
      :min="min"
      :max="max"
      :step="step"
      :inputmode="inputmode"
      :class="INPUT_CLASS"
      @input="onInput"
    />
    <span v-if="hint" class="font-body-sm text-body-sm text-outline">{{ hint }}</span>
  </div>
</template>
