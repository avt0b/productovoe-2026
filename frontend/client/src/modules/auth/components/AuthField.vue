<script setup lang="ts">
import { useId } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

const model = defineModel<string>({ required: true })

withDefaults(
  defineProps<{
    label: string
    icon: string
    placeholder?: string
    type?: 'text' | 'password' | 'email'
    autocomplete?: string
    /**
     * Какую клавиатуру открыть на телефоне. Для чисел — `numeric` при
     * `type="text"`, а не `type="number"`: у того колесо мыши меняет
     * значение и пропускается буква «e».
     */
    inputmode?: 'text' | 'numeric' | 'email'
    maxlength?: number
  }>(),
  { type: 'text', placeholder: '', autocomplete: 'off', inputmode: undefined, maxlength: undefined },
)

defineSlots<{
  /** Кнопка внутри поля справа — «показать пароль». */
  trailing?: () => unknown
}>()

const id = useId()
</script>

<template>
  <div class="flex flex-col space-y-space-xs">
    <label :for="id" class="font-label-md text-label-md text-white/70">{{ label }}</label>
    <!--
      Поле — строка, а не коробка: на фотографии рамка вокруг каждой графы
      превращала форму в решётку. Остаётся одна линия снизу, в фокусе она
      светлеет — так видно, какую графу сейчас заполняют.
    -->
    <div
      class="flex items-center border-b border-white/25 py-2.5 text-white transition-colors focus-within:border-white short:py-2"
    >
      <MsIcon :name="icon" :size="18" class="mr-space-sm text-white/55" />
      <input
        :id="id"
        v-model="model"
        :type="type"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        :inputmode="inputmode"
        :maxlength="maxlength"
        class="w-full border-none bg-transparent font-body-md text-body-md text-white outline-none placeholder:text-white/45 focus-visible:ring-0 focus-visible:ring-offset-0"
      />
      <slot name="trailing" />
    </div>
  </div>
</template>
