<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <label class="relative inline-flex items-center cursor-pointer shrink-0">
    <input
      type="checkbox"
      class="sr-only peer"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <div
      class="w-11 h-6 bg-surface-container-high peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-secondary"
    />
  </label>
</template>
