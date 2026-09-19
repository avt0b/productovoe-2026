<script setup lang="ts">
import { useId } from 'vue'

import { INPUT_CLASS } from './styles'

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
  <div class="flex min-w-0 flex-col gap-1">
    <label :for="id" class="font-label-md text-label-md text-on-surface">{{ label }}</label>
    <textarea
      :id="id"
      v-model="model"
      :rows="rows"
      :placeholder="placeholder"
      :required="required"
      :maxlength="maxlength"
      :class="INPUT_CLASS"
    />
    <span v-if="hint" class="font-body-sm text-body-sm text-outline">{{ hint }}</span>
  </div>
</template>
