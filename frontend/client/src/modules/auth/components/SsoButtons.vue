<script setup lang="ts">
import { computed } from 'vue'

import type { ExternalProvider, ProviderInfo } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Вход через VK ID, Яндекс ID, Госуслуги и MAX. Что включено на сервере,
 * решает `auth_service` (`/auth/external/providers`): выключенную кнопку не
 * нажать — лучше честно недоступная, чем молчащая.
 */
const props = defineProps<{
  /** Что умеет сервер входа. `null` — список не пришёл: сервер не ответил. */
  providers: ProviderInfo[] | null
  /** Способ входа, который сейчас в работе, — крутилка только на нём. */
  active: ExternalProvider | null
  disabled: boolean
}>()

defineEmits<{ select: [provider: ExternalProvider] }>()

/**
 * Кнопки стоят на фоновом снимке, поэтому плашки белые, а не по поверхности темы.
 * У VK ID и Яндекс ID — монограмма: по ней сервис узнают быстрее, чем по
 * значку из общего набора, а фирменные цвета мимо палитры контракт не пускает.
 */
const LOOK: readonly { provider: ExternalProvider; title: string; mark?: string; icon?: string; tone: string }[] = [
  { provider: 'vk', title: 'VK ID', mark: 'VK', tone: 'text-secondary' },
  { provider: 'yandex', title: 'Яндекс ID', mark: 'Я', tone: 'text-primary' },
  { provider: 'gosuslugi', title: 'Госуслуги', icon: 'account_balance', tone: 'text-tertiary' },
  { provider: 'max', title: 'MAX', icon: 'chat', tone: 'text-on-surface' },
]

const buttons = computed(() =>
  LOOK.map((look) => ({ ...look, enabled: props.providers?.find((item) => item.provider === look.provider)?.enabled ?? false })),
)
</script>

<template>
  <div class="grid grid-cols-4 gap-space-xs">
    <button
      v-for="(button, index) in buttons"
      :key="button.provider"
      type="button"
      class="flex min-w-0 flex-col items-center justify-center rounded-lg border border-white/20 bg-white/10 px-1 py-2.5 backdrop-blur-sm transition-colors hover:border-white/40 hover:bg-white/20 active:scale-95 disabled:opacity-50 short:py-2"
      :disabled="disabled || !button.enabled"
      :title="button.enabled ? undefined : 'Этот способ входа на сервере не настроен'"
      :aria-label="`Войти через ${button.title}`"
      @click="$emit('select', button.provider)"
    >
      <div class="mb-1 flex h-7 w-7 items-center justify-center rounded-full bg-white/90" :class="button.tone">
        <MsIcon v-if="active === button.provider" name="progress_activity" :size="15" class="animate-spin" />
        <span v-else-if="button.mark" class="font-label-md text-label-md font-extrabold leading-none" aria-hidden="true">
          {{ button.mark }}
        </span>
        <MsIcon v-else :name="button.icon ?? 'login'" :size="15" />
      </div>
      <span
        class="ribbon-shimmer w-full truncate text-center font-label-sm text-label-sm text-white"
        :style="{ animationDelay: `${2000 + index * 260}ms` }"
        >{{ button.title }}</span
      >
    </button>
  </div>
</template>
