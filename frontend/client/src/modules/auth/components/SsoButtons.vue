<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

defineProps<{ disabled: boolean }>()

defineEmits<{ select: [provider: { id: string; title: string }] }>()

/**
 * Внешние провайдеры входа. Обмена токенами за ними пока нет: кнопка сообщает
 * наверх, какой способ выбрали, а экран входа объясняет, что он не подключён.
 */
const providers = [
  { id: 'gosuslugi', title: 'Госуслуги', icon: 'account_balance', tone: 'bg-white/90 text-primary' },
  { id: 'vk-id', title: 'VK ID', icon: 'share', tone: 'bg-white/90 text-secondary' },
  { id: 'sber-id', title: 'Сбер ID', icon: 'payments', tone: 'bg-white/90 text-tertiary' },
] as const satisfies readonly { id: string; title: string; icon: string; tone: string }[]
</script>

<template>
  <div class="grid grid-cols-3 gap-space-sm">
    <button
      v-for="(provider, index) in providers"
      :key="provider.id"
      type="button"
      class="flex flex-col items-center justify-center rounded-lg border border-white/20 bg-white/10 px-1 py-2.5 backdrop-blur-sm transition-colors hover:border-white/40 hover:bg-white/20 disabled:opacity-60 short:py-2"
      :disabled="disabled"
      @click="$emit('select', { id: provider.id, title: provider.title })"
    >
      <div class="mb-1 flex h-7 w-7 items-center justify-center rounded-full" :class="provider.tone">
        <MsIcon :name="provider.icon" :size="15" />
      </div>
      <span
        class="ribbon-shimmer truncate font-label-sm text-label-sm text-white"
        :style="{ animationDelay: `${2000 + index * 260}ms` }"
        >{{ provider.title }}</span
      >
    </button>
  </div>
</template>
