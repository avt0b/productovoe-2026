<script setup lang="ts">
import { computed, ref } from 'vue'

import { formatMoney, plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { Campaign } from '../data'

const props = defineProps<{ campaign: Campaign }>()

const percent = computed(() => Math.min(100, Math.round((props.campaign.raised / props.campaign.goal) * 100)))

const daysLeft = computed(
  () => `Осталось ${props.campaign.daysLeft} ${plural(props.campaign.daysLeft, ['день', 'дня', 'дней'])}`,
)

const supporters = computed(() => {
  const count = props.campaign.supporters
  return `${count} ${plural(count, ['человек', 'человека', 'человек'])} уже ${count % 10 === 1 && count % 100 !== 11 ? 'помог' : 'помогли'} отряду`
})

/**
 * Оплаты пока нет. Показывать «Спасибо за поддержку!», когда деньги никуда не
 * ушли, значит обмануть человека, — поэтому кнопка честно говорит, что будет.
 */
const donateNotice = ref(false)
</script>

<template>
  <article class="relative flex flex-col gap-4 rounded-lg bg-surface-container-lowest p-5 shadow-sm">
    <div class="flex items-center justify-between gap-2">
      <span
        v-if="campaign.urgent"
        class="flex items-center gap-1 rounded-full bg-primary-fixed px-3 py-1 font-label-sm text-label-sm text-on-primary-fixed-variant"
      >
        <span class="h-2 w-2 animate-pulse rounded-full bg-primary" />
        Срочный сбор
      </span>
      <span class="flex items-center gap-1 font-label-sm text-label-sm text-outline">
        <MsIcon name="schedule" :size="16" />
        {{ daysLeft }}
      </span>
    </div>

    <div class="flex items-center gap-3">
      <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-secondary-container text-secondary">
        <MsIcon name="flag" />
      </div>
      <div class="min-w-0">
        <h3 class="truncate font-headline-sm text-headline-sm text-on-surface">{{ campaign.squad }}</h3>
        <p class="flex items-center gap-1 font-body-sm text-body-sm text-outline">
          <MsIcon name="location_on" :size="14" />{{ campaign.city }}
        </p>
      </div>
    </div>

    <div class="rounded-DEFAULT bg-surface-container-low p-3.5">
      <p class="font-body-md text-body-md leading-snug text-on-surface">{{ campaign.purpose }}</p>
    </div>

    <div class="flex flex-col gap-2">
      <div class="flex items-baseline justify-between">
        <span class="font-headline-sm text-headline-sm font-extrabold text-on-surface">{{ formatMoney(campaign.raised) }}</span>
        <span class="font-body-sm text-body-sm text-outline">из {{ formatMoney(campaign.goal) }} ({{ percent }}%)</span>
      </div>
      <div
        class="h-3 w-full overflow-hidden rounded-full bg-surface-container-high p-0.5"
        role="progressbar"
        :aria-valuenow="percent"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Собрано ${percent}%`"
      >
        <div class="h-full rounded-full bg-primary-container transition-all duration-500" :style="{ width: `${percent}%` }" />
      </div>
      <div class="mt-1 flex items-center gap-2">
        <div class="flex -space-x-2">
          <span
            v-for="(initials, index) in campaign.supporterInitials"
            :key="initials"
            class="flex h-6 w-6 items-center justify-center rounded-full font-label-sm text-label-sm"
            :class="index % 2 === 0 ? 'bg-tertiary-fixed text-on-tertiary-fixed' : 'bg-secondary-fixed text-on-secondary-fixed'"
          >
            {{ initials }}
          </span>
          <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary-fixed font-label-sm text-label-sm text-on-primary-fixed">
            +
          </span>
        </div>
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ supporters }}</span>
      </div>
    </div>

    <button
      type="button"
      class="flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3.5 font-label-lg text-label-lg text-on-primary shadow-md shadow-primary/25 transition-all hover:brightness-105 active:scale-[0.98]"
      @click="donateNotice = true"
    >
      <MsIcon name="volunteer_activism" :size="20" filled />
      Помочь отряду (от {{ formatMoney(campaign.minDonation) }})
    </button>
    <p
      v-if="donateNotice"
      class="flex items-start gap-2 rounded-DEFAULT bg-surface-container-low px-3 py-2 font-body-sm text-body-sm text-on-surface-variant"
      role="status"
    >
      <MsIcon name="info" :size="18" class="mt-0.5 shrink-0 text-primary" />
      Оплату через ЮKassa подключим следующим шагом — пока деньги не списываются.
    </p>
  </article>
</template>
