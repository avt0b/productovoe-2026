<script setup>
import { ref } from 'vue'

const emit = defineEmits(['success'])

const providers = [
  { id: 'vk', label: 'ВКонтакте', bg: 'bg-[#0077FF]', fg: 'text-white', short: 'VK' },
  { id: 'yandex', label: 'Яндекс ID', bg: 'bg-[#FC3F1D]', fg: 'text-white', short: 'Я' },
  { id: 'gosuslugi', label: 'Госуслуги', bg: 'bg-[#0F62AE]', fg: 'text-white', short: 'ГУ' },
]

const pending = ref(null)

function loginWith(id) {
  pending.value = id
  setTimeout(() => {
    pending.value = null
    emit('success')
  }, 900)
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center gap-3">
      <div class="h-px flex-1 bg-surface-container-high" />
      <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">или через</span>
      <div class="h-px flex-1 bg-surface-container-high" />
    </div>

    <div class="grid grid-cols-3 gap-2.5">
      <button
        v-for="provider in providers"
        :key="provider.id"
        type="button"
        class="h-12 rounded-full flex items-center justify-center gap-1.5 font-label-sm text-label-sm font-bold shadow-sm transition-transform hover:scale-[1.03] disabled:opacity-60"
        :class="[provider.bg, provider.fg]"
        :disabled="pending !== null"
        :title="provider.label"
        @click="loginWith(provider.id)"
      >
        <span v-if="pending === provider.id" class="material-symbols-outlined text-[18px] animate-spin">sync</span>
        <span v-else>{{ provider.short }}</span>
      </button>
    </div>
  </div>
</template>
