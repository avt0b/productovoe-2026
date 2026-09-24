<script setup>
import { useId } from 'vue'

defineProps({
  label: { type: String, required: true },
  icon: { type: String, required: true },
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  type: { type: String, default: 'text' },
  autocomplete: { type: String, default: 'off' },
})
defineEmits(['update:modelValue'])

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
    <div class="flex items-center border-b border-white/25 py-2.5 text-white transition-colors focus-within:border-white">
      <span class="material-symbols-outlined mr-space-sm text-[18px] text-white/55" aria-hidden="true">{{ icon }}</span>
      <input
        :id="id"
        :value="modelValue"
        :type="type"
        :placeholder="placeholder"
        :autocomplete="autocomplete"
        class="w-full border-none bg-transparent font-body-md text-body-md text-white outline-none placeholder:text-white/45"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <slot name="trailing" />
    </div>
  </div>
</template>
