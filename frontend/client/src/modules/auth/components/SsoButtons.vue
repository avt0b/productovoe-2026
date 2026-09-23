<script setup lang="ts">
import { computed } from 'vue'

import type { ExternalProvider, ProviderInfo } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

const props = defineProps<{
  /** Что умеет сервер входа. `null` — список не пришёл: сервер не ответил. */
  providers: ProviderInfo[] | null
  /** Способ входа, который сейчас в работе. */
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

/** Кнопки в своём порядке; доступность и «тест» — от сервера. */
const buttons = computed(() =>
  LOOK.map((look) => {
    const info = props.providers?.find((item) => item.provider === look.provider)
    return { ...look, enabled: info?.enabled ?? false, mock: info?.mock ?? false }
  }),
)
</script>

<template>
  <div class="grid grid-cols-3 gap-space-sm">
    <button
      v-for="(button, index) in buttons"
      :key="button.provider"
      type="button"
      class="relative flex flex-col items-center justify-center rounded-lg border border-white/20 bg-white/10 px-1 py-2.5 backdrop-blur-sm transition-colors hover:border-white/40 hover:bg-white/20 disabled:opacity-60 short:py-2"
      :disabled="disabled || !button.enabled"
      :title="button.enabled ? undefined : 'Этот способ входа на сервере не настроен'"
      @click="$emit('select', button.provider)"
    >
      <span
        v-if="button.mock"
        class="absolute right-1 top-1 rounded-full bg-tertiary-fixed px-1.5 font-label-sm text-label-sm text-on-tertiary-fixed"
      >
        тест
      </span>
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
