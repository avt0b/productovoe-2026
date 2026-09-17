<script setup lang="ts">
import type { SignInMethod } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

defineProps<{
  /** Способ входа, который сейчас в работе. */
  active: SignInMethod | null
  disabled: boolean
}>()

defineEmits<{ select: [method: SignInMethod] }>()

/** Внешние провайдеры входа. Пока все ведут в ту же заглушку, что и пароль. */
const providers = [
  { method: 'gosuslugi', title: 'Госуслуги', icon: 'account_balance', tone: 'bg-primary/10 text-primary' },
  { method: 'vk-id', title: 'VK ID', icon: 'share', tone: 'bg-secondary/15 text-secondary' },
  { method: 'sber-id', title: 'Сбер ID', icon: 'payments', tone: 'bg-secondary-fixed text-on-secondary-fixed' },
] as const satisfies readonly { method: SignInMethod; title: string; icon: string; tone: string }[]
</script>

<template>
  <div class="grid grid-cols-3 gap-space-sm">
    <button
      v-for="provider in providers"
      :key="provider.method"
      type="button"
      class="flex flex-col items-center justify-center rounded-xl bg-surface-container-low px-1 py-2.5 transition-colors hover:bg-surface-container disabled:opacity-60"
      :disabled="disabled"
      @click="$emit('select', provider.method)"
    >
      <div class="mb-1 flex h-7 w-7 items-center justify-center rounded-full" :class="provider.tone">
        <MsIcon
          :name="active === provider.method ? 'progress_activity' : provider.icon"
          :size="15"
          :class="{ 'animate-spin': active === provider.method }"
        />
      </div>
      <span class="truncate font-label-sm text-label-sm text-on-surface">{{ provider.title }}</span>
    </button>
  </div>
</template>
