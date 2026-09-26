<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import { timeAgo } from '../format'
import type { LostAlertController } from '../useLostAlert'

/** Карточка для ищущего: где потерявшийся, сколько до него, «Иду искать» и «Нашлись». */
const props = defineProps<{ lost: LostAlertController }>()

const alert = computed(() => props.lost.alert.value)
const name = computed(() => alert.value?.lost.display_name ?? 'Участник')
const responded = computed(() => props.lost.meWatcher.value?.responding ?? false)
const routeState = computed(() => props.lost.pointRoute.state.value)
const metersLeft = computed(() => props.lost.pointRoute.metersLeft.value)

const title = computed(() =>
  alert.value?.kind === 'self' ? `Потерялся участник: ${name.value}` : `Ищем участника: ${name.value}`,
)

const pointLine = computed(() => {
  const p = alert.value?.lost.position
  if (!p) return `«${name.value}» ещё не прислал(а), где находится — спросите у группы`
  const acc = p.accuracy_m != null ? ` · ± ${Math.round(p.accuracy_m)} м` : ''
  return `Последняя точка — ${timeAgo(p.updated_at, props.lost.now.value)}${acc}`
})

/** Другие ищущие, кроме меня, мелкой строкой. */
const others = computed(() =>
  (alert.value?.watchers ?? [])
    .filter((w) => !w.is_me)
    .map((w) => {
      if (!w.responding) return `${w.display_name} · не ответил`
      const dist = w.distance_m != null ? ` · ${w.distance_m} м` : ''
      return `${w.display_name} · идёт${dist}`
    }),
)
</script>

<template>
  <div class="flex flex-col gap-space-sm">
    <div class="flex min-w-0 flex-col">
      <p class="font-headline-sm text-headline-sm text-white">{{ title }}</p>
      <p class="truncate font-body-sm text-body-sm text-white/70">{{ alert?.excursion_title }}</p>
    </div>

    <p class="font-body-sm text-body-sm text-white/75">{{ pointLine }}</p>
    <p v-if="alert?.message" class="font-body-md text-body-md italic text-white/90">«{{ alert.message }}»</p>

    <p v-if="lost.actionError.value" class="rounded-xl bg-error/90 px-space-sm py-2 font-body-sm text-body-sm text-white" role="alert">
      {{ lost.actionError.value }}
    </p>

    <!-- Ещё не откликнулся: главное — пойти искать. -->
    <template v-if="!responded">
      <button
        type="button"
        class="flex h-11 items-center justify-center gap-space-xs rounded-full bg-primary-container font-label-lg text-label-lg text-white shadow-stamp transition-colors hover:bg-primary active:scale-[0.98] disabled:opacity-60"
        :disabled="lost.busy.value"
        @click="lost.respondAndGo()"
      >
        <MsIcon :name="lost.busy.value ? 'progress_activity' : 'directions_run'" :size="18" :class="{ 'animate-spin': lost.busy.value }" />
        Иду искать
      </button>
    </template>

    <!-- Откликнулся: маршрут уже на карте, показываем, сколько осталось. -->
    <template v-else>
      <p v-if="routeState === 'arrived'" class="font-label-lg text-label-lg text-tertiary-fixed-dim">
        Вы рядом — видите «{{ name }}»?
      </p>
      <p v-else-if="metersLeft !== null" class="font-label-lg text-label-lg text-white">
        Осталось {{ Math.round(metersLeft ?? 0) }} м
      </p>
    </template>

    <button
      type="button"
      class="flex h-11 items-center justify-center gap-space-xs rounded-full font-label-lg text-label-lg active:scale-[0.98] disabled:opacity-60"
      :class="responded ? 'bg-tertiary text-on-tertiary shadow-stamp hover:bg-tertiary/90' : 'border border-white/20 bg-white/10 text-white hover:bg-white/20'"
      :disabled="lost.busy.value"
      @click="lost.resolve()"
    >
      <MsIcon :name="lost.busy.value ? 'progress_activity' : 'celebration'" :size="18" :class="{ 'animate-spin': lost.busy.value }" />
      Нашлись!
    </button>

    <div v-if="others.length" class="flex flex-col gap-0.5 pt-space-xs">
      <p v-for="(line, i) in others" :key="i" class="font-body-sm text-body-sm text-white/60">{{ line }}</p>
    </div>
  </div>
</template>
