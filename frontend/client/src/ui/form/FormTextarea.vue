<script setup lang="ts">
import { useId } from 'vue'

import { FIELD_HINT_CLASS, FIELD_LABEL_CLASS, TEXTAREA_CLASS } from './styles'

const model = defineModel<string>({ required: true })

withDefaults(
  defineProps<{
    label: string
    placeholder?: string
    hint?: string
    rows?: number
    required?: boolean
    maxlength?: number
  }>(),
  { placeholder: '', hint: '', rows: 3, required: false, maxlength: undefined },
)

const id = useId()
</script>

<template>
  <div class="flex min-w-0 flex-col space-y-space-xs">
    <label :for="id" :class="FIELD_LABEL_CLASS">{{ label }}</label>
    <textarea
      :id="id"
      v-model="model"
      :rows="rows"
      :placeholder="placeholder"
      :required="required"
      :maxlength="maxlength"
      :class="TEXTAREA_CLASS"
    />
    <span v-if="hint" :class="FIELD_HINT_CLASS">{{ hint }}</span>
  </div>
</template>
