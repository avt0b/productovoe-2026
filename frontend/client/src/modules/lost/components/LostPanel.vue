<script setup lang="ts">
import { computed, watchEffect } from 'vue'

import { usePreferencesStore } from '@/core/preferences'
import ConfirmAction from '@/ui/ConfirmAction.vue'
import MsIcon from '@/ui/MsIcon.vue'

import type { LostAlertController } from '../useLostAlert'

/** Карточка для потерявшегося: кто идёт, совет стоять на месте, «Меня нашли» и «Отбой». */
const props = defineProps<{ lost: LostAlertController }>()

const preferences = usePreferencesStore()
const family = computed(() => preferences.familyMode)

const alert = computed(() => props.lost.alert.value)
const responders = computed(() => props.lost.responders.value)
const nearest = computed(() => props.lost.nearestResponder.value)

const title = computed(() => (family.value ? 'Тебя ищут' : 'Вас ищут'))
const you = computed(() => (family.value ? 'тебе' : 'вам'))

/** Имена всех ищущих — для «Тревога у: …», пока никто не откликнулся. */
const waitingLine = computed(() => {
  const names = (alert.value?.watchers ?? []).map((w) => w.display_name).join(', ')
  return `Тревога у: ${names}. Ждём, кто откликнется.`
})

const advice = computed(() => {
  if (!nearest.value) return 'Стой на месте. Взрослые уже знают, что ты потерялся(-ась).'
  return `Стой на месте и никуда не уходи. ${nearest.value.display_name} видит тебя на карте и уже идёт.`
})

// Обычный режим: маршрут к ближайшему включается сам; семейный — только по кнопке.
watchEffect(() => {
  if (!family.value && props.lost.active.value && !props.lost.pointRoute.target.value && props.lost.routeGoal.value) {
    props.lost.startRoute()
  }
})
</script>

<template>
  <div class="flex flex-col gap-space-sm">
    <p class="font-headline-sm text-headline-sm text-white">{{ title }}</p>

    <p v-if="responders.length === 0" class="font-body-md text-body-md text-white/80">{{ waitingLine }}</p>
    <div v-else class="flex flex-col gap-space-xs">
      <p v-for="w in responders" :key="w.user_id" class="font-label-lg text-label-lg text-white">
        {{ w.display_name }} идёт к {{ you }}<span v-if="w.distance_m != null"> · {{ w.distance_m }} м</span>
      </p>
    </div>

    <!-- Семейный режим: крупный совет, маршрут только по кнопке. -->
    <template v-if="family">
      <div class="flex items-start gap-space-sm rounded-xl bg-white/10 p-space-sm">
        <MsIcon name="pin_drop" :size="22" class="mt-0.5 shrink-0 text-tertiary-fixed-dim" />
        <p class="font-body-md text-body-md text-white">{{ advice }}</p>
      </div>
    </template>

    <p v-if="lost.actionError.value" class="rounded-xl bg-error/90 px-space-sm py-2 font-body-sm text-body-sm text-white" role="alert">
      {{ lost.actionError.value }}
    </p>

    <button
      type="button"
      class="flex h-11 items-center justify-center gap-space-xs rounded-full bg-tertiary font-label-lg text-label-lg text-on-tertiary shadow-stamp transition-colors hover:bg-tertiary/90 active:scale-[0.98] disabled:opacity-60"
      :disabled="lost.busy.value"
      @click="lost.resolve()"
    >
      <MsIcon :name="lost.busy.value ? 'progress_activity' : 'celebration'" :size="18" :class="{ 'animate-spin': lost.busy.value }" />
      Меня нашли
    </button>

    <button
      v-if="family && nearest"
      type="button"
      class="flex h-11 items-center justify-center gap-space-xs rounded-full border border-white/20 bg-white/10 font-label-lg text-label-lg text-white transition-colors hover:bg-white/20 active:scale-[0.98]"
      @click="lost.startRoute()"
    >
      <MsIcon name="directions" :size="18" />
      <!-- Имя в кавычках, как в уведомлениях: имена не склоняем, «к Мама» резало бы глаз. -->
      Показать дорогу к «{{ nearest.display_name }}»
    </button>

    <ConfirmAction
      label="Отбой — я не потерялся(-ась)"
      icon="close"
      warning="Семья и краевед увидят, что поиск отменён"
      confirm-label="Да, отбой тревоги"
      tone="neutral"
      :busy="lost.busy.value"
      @confirm="lost.cancel()"
    />
  </div>
</template>
