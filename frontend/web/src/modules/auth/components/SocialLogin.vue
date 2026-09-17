<script setup>
import { ref } from 'vue'

const providers = [
  { id: 'vk', label: 'ВКонтакте', bg: 'bg-[#0077FF]', fg: 'text-white', short: 'VK' },
  { id: 'yandex', label: 'Яндекс ID', bg: 'bg-[#FC3F1D]', fg: 'text-white', short: 'Я' },
  { id: 'gosuslugi', label: 'Госуслуги', bg: 'bg-[#0F62AE]', fg: 'text-white', short: 'ГУ' },
]

const notice = ref('')
let hideTimer

function announceComingSoon(provider) {
  notice.value = `Вход через ${provider.label} скоро появится — пока доступен вход по e-mail`
  clearTimeout(hideTimer)
  hideTimer = setTimeout(() => {
    notice.value = ''
  }, 3500)
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
        class="h-12 rounded-full flex items-center justify-center gap-1.5 font-label-sm text-label-sm font-bold shadow-sm transition-transform hover:scale-[1.03]"
        :class="[provider.bg, provider.fg]"
        :title="`${provider.label} — скоро`"
        @click="announceComingSoon(provider)"
      >
        <span>{{ provider.short }}</span>
      </button>
    </div>

    <Transition
      enter-active-class="transition-all duration-200"
      leave-active-class="transition-all duration-200"
      enter-from-class="opacity-0 -translate-y-1"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <p
        v-if="notice"
        class="flex items-center gap-1.5 justify-center text-center font-label-sm text-label-sm text-on-surface-variant bg-surface-container-low rounded-full px-3 py-2"
      >
        <span class="material-symbols-outlined text-[16px] text-secondary">schedule</span>
        {{ notice }}
      </p>
    </Transition>
  </div>
</template>
