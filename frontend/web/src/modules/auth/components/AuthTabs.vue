<script setup>
defineProps({
  modelValue: { type: String, required: true },
})
defineEmits(['update:modelValue'])

const tabs = [
  { id: 'login', label: 'Вход' },
  { id: 'register', label: 'Регистрация' },
]
</script>

<template>
  <div class="grid grid-cols-2 bg-surface-container-low rounded-full p-1">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="py-2.5 rounded-full font-label-lg text-label-lg font-bold transition-all"
      :class="modelValue === tab.id ? 'bg-primary text-on-primary shadow-sm' : 'text-on-surface-variant hover:text-on-surface'"
      @click="$emit('update:modelValue', tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
