<script setup lang="ts">
import { useId } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import { FIELD_HINT_CLASS, FIELD_LABEL_CLASS, FIELD_LINE_CLASS, INPUT_CLASS } from './styles'

/**
 * Поле формы с подписью.
 *
 * У `type="number"` модель — число (пустое поле — `null`), у остальных — строка.
 */
const model = defineModel<string | number | null>({ required: true })

const props = withDefaults(
  defineProps<{
    label: string
    /** Иконка Material Symbols слева в строке. Без неё графа просто начинается с текста. */
    icon?: string
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
    icon: undefined,
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
  <div class="flex min-w-0 flex-col space-y-space-xs">
    <label :for="id" :class="FIELD_LABEL_CLASS">{{ label }}</label>
    <div :class="FIELD_LINE_CLASS">
      <MsIcon v-if="icon" :name="icon" :size="18" class="shrink-0 text-on-surface-variant" />
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
      <!-- Единица измерения, кнопка «показать пароль», «сейчас» у даты. -->
      <slot name="trailing" />
    </div>
    <span v-if="hint" :class="FIELD_HINT_CLASS">{{ hint }}</span>
  </div>
</template>
