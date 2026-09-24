<script setup lang="ts">
import { computed } from 'vue'

import type { ExternalProvider, ProviderInfo } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Вход через VK ID, MAX и Госуслуги. Что включено на сервере, решает
 * `auth_service` (`/auth/external/providers`): выключенную кнопку не нажать —
 * лучше честно недоступная, чем молчащая.
 */
const props = defineProps<{
  /** Что умеет сервер входа. `null` — список не пришёл: сервер не ответил. */
  providers: ProviderInfo[] | null
  /** Способ входа, который сейчас в работе, — крутилка только на нём. */
  active: ExternalProvider | null
  disabled: boolean
}>()

defineEmits<{ select: [provider: ExternalProvider] }>()

/** Кнопки стоят на фоновом снимке, поэтому плашки белые, а не по поверхности темы. */
const LOOK: readonly { provider: ExternalProvider; title: string; icon: string; tone: string }[] = [
  { provider: 'gosuslugi', title: 'Госуслуги', icon: 'account_balance', tone: 'bg-white/90 text-primary' },
  { provider: 'vk', title: 'VK ID', icon: 'share', tone: 'bg-white/90 text-secondary' },
  { provider: 'max', title: 'MAX', icon: 'chat', tone: 'bg-white/90 text-tertiary' },
]

const buttons = computed(() =>
  LOOK.map((look) => ({ ...look, enabled: props.providers?.find((item) => item.provider === look.provider)?.enabled ?? false })),
)
</script>

<template>
  <div class="grid grid-cols-3 gap-space-sm">
    <button
      v-for="(button, index) in buttons"
      :key="button.provider"
      type="button"
      class="flex flex-col items-center justify-center rounded-lg border border-white/20 bg-white/10 px-1 py-2.5 backdrop-blur-sm transition-colors hover:border-white/40 hover:bg-white/20 disabled:opacity-50 short:py-2"
      :disabled="disabled || !button.enabled"
      :title="button.enabled ? undefined : 'Этот способ входа на сервере не настроен'"
      @click="$emit('select', button.provider)"
    >
      <div class="mb-1 flex h-7 w-7 items-center justify-center rounded-full" :class="button.tone">
        <MsIcon
          :name="active === button.provider ? 'progress_activity' : button.icon"
          :size="15"
          :class="{ 'animate-spin': active === button.provider }"
        />
      </div>
      <span
        class="ribbon-shimmer truncate font-label-sm text-label-sm text-white"
        :style="{ animationDelay: `${2000 + index * 260}ms` }"
        >{{ button.title }}</span
      >
    </button>
  </div>
</template>
