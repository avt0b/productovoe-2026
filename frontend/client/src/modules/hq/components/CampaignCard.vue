<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import { formatMoney } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { CAMPAIGN_KINDS, campaignOf, type Need, type Squad } from '../data'

const props = defineProps<{
  need: Need
  squad: Squad | undefined
  /** Командир этого отряда или модератор: может закрыть сбор. */
  canManage: boolean
  closing?: boolean
}>()

const emit = defineEmits<{ donate: []; close: [] }>()

const campaign = computed(() => campaignOf(props.need))
const kind = computed(() => CAMPAIGN_KINDS[campaign.value.kind])
const isOpen = computed(() => props.need.status === 'open')

const percent = computed(() => {
  const target = props.need.target_amount
  return target ? Math.min(100, Math.round((props.need.collected_amount / target) * 100)) : null
})
const left = computed(() => {
  const target = props.need.target_amount
  return target ? Math.max(0, target - props.need.collected_amount) : null
})

/** Закрыть сбор нельзя отменить — поэтому сначала спрашиваем, прямо в карточке. */
const confirming = ref(false)

const shared = ref(false)
let sharedTimer: ReturnType<typeof setTimeout> | undefined

/**
 * Поделиться сбором. В WebView Android нет `navigator.share` — тогда текст
 * уходит в буфер, и его можно вставить в любой мессенджер.
 */
async function share(): Promise<void> {
  const progress = props.need.target_amount
    ? `собрано ${formatMoney(props.need.collected_amount)} из ${formatMoney(props.need.target_amount)}`
    : `собрано ${formatMoney(props.need.collected_amount)}`
  const text = `${props.need.title} — ${progress}. ${props.squad?.name ?? 'Поисковый отряд'}. Помочь можно в приложении «Маршруты победы».`
  try {
    if (navigator.share) {
      await navigator.share({ title: props.need.title, text })
      return
    }
    await navigator.clipboard.writeText(text)
    shared.value = true
    clearTimeout(sharedTimer)
    sharedTimer = setTimeout(() => (shared.value = false), 2000)
  } catch {
    /* человек закрыл окно «Поделиться» — это не ошибка */
  }
}

onBeforeUnmount(() => clearTimeout(sharedTimer))
</script>

<template>
  <article class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <div class="flex items-center justify-between gap-space-sm">
      <p class="flex min-w-0 items-center gap-1 font-archival text-archival uppercase text-on-surface-variant">
        <MsIcon :name="kind.icon" :size="15" class="shrink-0 text-tertiary" />
        <span class="truncate">{{ kind.title }}</span>
      </p>
      <span
        v-if="isOpen"
        class="flex shrink-0 items-center gap-1.5 rounded-full bg-secondary-container px-2.5 py-0.5 font-label-sm text-label-sm text-on-secondary-container"
      >
        <span class="h-1.5 w-1.5 rounded-full bg-secondary motion-safe:animate-pulse" />
        Идёт сбор
      </span>
      <span v-else class="shrink-0 rounded-full bg-surface-container-high px-2.5 py-0.5 font-label-sm text-label-sm text-on-surface-variant">
        Сбор закрыт
      </span>
    </div>

    <div>
      <h3 class="font-headline-sm text-headline-sm text-on-surface">{{ campaign.headline }}</h3>
      <p class="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
        <MsIcon name="flag" :size="15" class="shrink-0 text-secondary" />
        <span class="truncate">{{ [squad?.name ?? 'Поисковый отряд', squad?.region].filter(Boolean).join(' · ') }}</span>
      </p>
    </div>

    <p v-if="need.description" class="font-body-sm text-body-sm text-on-surface-variant">{{ need.description }}</p>

    <div class="flex flex-col gap-space-xs">
      <div class="flex items-baseline justify-between gap-space-sm">
        <span class="font-headline-md text-headline-md text-on-surface">{{ formatMoney(need.collected_amount) }}</span>
        <span v-if="need.target_amount" class="font-label-md text-label-md text-on-surface-variant">из {{ formatMoney(need.target_amount) }}</span>
      </div>
      <template v-if="percent !== null">
        <div
          class="h-2 w-full overflow-hidden rounded-full bg-surface-container-high"
          role="progressbar"
          :aria-valuenow="percent"
          aria-valuemin="0"
          aria-valuemax="100"
          :aria-label="`Собрано ${percent}%`"
        >
          <div class="h-full rounded-full bg-secondary transition-[width] duration-500 ease-out" :style="{ width: `${percent}%` }" />
        </div>
        <div class="flex justify-between gap-space-sm font-label-sm text-label-sm text-on-surface-variant">
          <span>{{ percent }}% собрано</span>
          <span v-if="left">осталось {{ formatMoney(left) }}</span>
          <span v-else class="text-secondary">цель достигнута</span>
        </div>
      </template>
    </div>

    <div v-if="isOpen" class="flex items-center gap-space-xs">
      <button
        type="button"
        class="flex flex-1 items-center justify-center gap-space-xs rounded-full bg-secondary px-space-md py-2.5 font-label-lg text-label-lg text-on-secondary transition-all hover:brightness-105 active:scale-[0.99]"
        @click="emit('donate')"
      >
        <MsIcon name="volunteer_activism" :size="18" filled />
        Помочь отряду
      </button>
      <button
        type="button"
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface transition-colors duration-200 active:scale-95"
        :aria-label="shared ? 'Текст сбора скопирован' : 'Поделиться сбором'"
        @click="share"
      >
        <MsIcon :name="shared ? 'check' : 'share'" :size="18" />
      </button>
    </div>

    <div v-if="isOpen && canManage" class="flex flex-col">
      <button
        type="button"
        class="self-center font-label-md text-label-md text-on-surface-variant underline-offset-2 hover:underline"
        :aria-expanded="confirming"
        @click="confirming = !confirming"
      >
        Закрыть сбор
      </button>
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="confirming ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!confirming"
      >
        <div class="overflow-hidden">
          <div class="mt-space-xs flex items-center justify-between gap-space-sm rounded-2xl bg-surface-container-low px-space-sm py-2">
            <span class="font-body-sm text-body-sm text-on-surface">Закрыть сбор? Вернуть его будет нельзя.</span>
            <div class="flex shrink-0 gap-space-xs">
              <button
                type="button"
                class="rounded-full px-space-sm py-1.5 font-label-md text-label-md text-on-surface-variant active:scale-95"
                @click="confirming = false"
              >
                Нет
              </button>
              <button
                type="button"
                class="flex items-center gap-1 rounded-full bg-surface-container-high px-space-sm py-1.5 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
                :disabled="closing"
                @click="emit('close')"
              >
                <MsIcon v-if="closing" name="progress_activity" :size="15" class="animate-spin" />
                Закрыть
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </article>
</template>
