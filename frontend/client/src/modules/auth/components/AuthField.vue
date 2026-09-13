<script setup lang="ts">
import { useId } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

const model = defineModel<string>({ required: true })

withDefaults(
  defineProps<{
    label: string
    icon: string
    placeholder?: string
    type?: 'text' | 'password'
    autocomplete?: string
  }>(),
  { type: 'text', placeholder: '', autocomplete: 'off' },
)

defineSlots<{
  /** Ссылка справа от подписи — «Забыли пароль?». */
  'label-action'?: () => unknown
  /** Кнопка внутри поля справа — «показать пароль». */
  trailing?: () => unknown
}>()

const id = useId()
</script>

<template>
  <div class="flex flex-col space-y-space-xs">
    <div class="flex items-center justify-between">
      <label :for="id" class="font-label-md text-label-md text-on-surface-variant">{{ label }}</label>
      <slot name="label-action" />
    </div>
    <div
      class="flex items-center rounded-full bg-surface-container-low px-space-md py-3 text-on-surface focus-within:bg-surface-container"
    >
      <MsIcon :name="icon" :size="18" class="mr-space-sm text-outline" />
      <input
        :id="id"
        v-model="model"
        :type="type"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        class="w-full border-none bg-transparent font-body-md text-body-md text-on-surface outline-none placeholder:text-outline/70"
      />
      <slot name="trailing" />
    </div>
  </div>
</template>
