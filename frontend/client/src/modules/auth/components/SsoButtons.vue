<script setup lang="ts">
/**
 * Альтернативные способы входа. Пока это заглушка: кнопки стоят в макете, но
 * ничего не делают — сами провайдеры (VK ID, MAX, Госуслуги) на проде ещё не
 * подключены, а показывать «тест» или гасить кнопки на экране входа незачем.
 * Когда провайдеров включат, сюда вернутся `providers`/`active` и событие выбора.
 */
import MsIcon from '@/ui/MsIcon.vue'

/** Кнопки стоят на фоновом снимке, поэтому плашки белые, а не по поверхности темы. */
const BUTTONS: readonly { id: string; title: string; icon: string; tone: string }[] = [
  { id: 'gosuslugi', title: 'Госуслуги', icon: 'account_balance', tone: 'bg-white/90 text-primary' },
  { id: 'vk', title: 'VK ID', icon: 'share', tone: 'bg-white/90 text-secondary' },
  { id: 'max', title: 'MAX', icon: 'chat', tone: 'bg-white/90 text-tertiary' },
]
</script>

<template>
  <div class="grid grid-cols-3 gap-space-sm">
    <button
      v-for="(button, index) in BUTTONS"
      :key="button.id"
      type="button"
      class="flex flex-col items-center justify-center rounded-lg border border-white/20 bg-white/10 px-1 py-2.5 backdrop-blur-sm transition-colors hover:border-white/40 hover:bg-white/20 short:py-2"
    >
      <div class="mb-1 flex h-7 w-7 items-center justify-center rounded-full" :class="button.tone">
        <MsIcon :name="button.icon" :size="15" />
      </div>
      <span
        class="ribbon-shimmer truncate font-label-sm text-label-sm text-white"
        :style="{ animationDelay: `${2000 + index * 260}ms` }"
        >{{ button.title }}</span
      >
    </button>
  </div>
</template>
