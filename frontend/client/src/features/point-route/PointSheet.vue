<script setup lang="ts">
import { Browser } from '@capacitor/browser'
import { Capacitor } from '@capacitor/core'
import { computed, ref } from 'vue'

import { directionsUrl, distanceKm, formatDistance, formatWalkDuration } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'

import type { PointRoute, PointRouteState, RouteTarget } from './usePointRoute'

/**
 * Карточка точки внизу раскрытой карты: что это за место и как до него
 * добраться. «Начать маршрут» сам определяет, где человек, и прокладывает
 * путь на карте окна; дальше можно передать его в Яндекс Карты.
 *
 * Карточка лежит на карте, поэтому она из тёмного стекла — как панель на
 * карте идущей группы. Действия конкретного окна («Поправить», «Открыть
 * точку») приходят слотом.
 */
const props = defineProps<{
  point: RouteTarget
  /** Маршрут окна — один на карту, карточка лишь показывает его и управляет им. */
  routing: PointRoute
  /** Рубрика над заголовком: вид места, стадия находки. */
  kicker: string
  icon: string
  title: string
  /** Короткие строки под заголовком: дата, источник. */
  facts?: { icon: string; text: string }[]
  description?: string
}>()

defineEmits<{ close: [] }>()

const { target, route, mode, state: routeState, problem, position } = props.routing

/** Маршрут сейчас ведёт именно сюда. К другой точке — для этой его как будто нет. */
const mine = computed(() => target.value?.id === props.point.id)
const state = computed<PointRouteState>(() => (mine.value ? routeState.value : 'idle'))

/** Длинное описание сворачиваем в три строки: карточка не должна закрывать всю карту. */
const LONG_DESCRIPTION = 160
const expanded = ref(false)

const fromMe = computed(() => {
  const me = position.value
  return me ? formatDistance(distanceKm(me, props.point)) : null
})

const summary = computed(() => {
  const current = route.value
  if (!current) return ''
  const how = current.estimated ? 'по прямой' : current.mode === 'car' ? 'на машине' : 'пешком'
  return `${formatDistance(current.distanceMeters / 1000)} · ${formatWalkDuration(current.durationSeconds)} ${how}`
})

function start(): void {
  props.routing.start(props.point)
}

/** Тот же маршрут во внешнем навигаторе: голосом и с поворотами. */
async function openNavigator(): Promise<void> {
  const url = directionsUrl(position.value, props.point, mode.value)
  if (Capacitor.isNativePlatform()) await Browser.open({ url })
  else window.open(url, '_blank', 'noopener')
}
</script>

<template>
  <section
    class="flex max-h-[55vh] flex-col gap-space-sm overflow-y-auto rounded-2xl border border-white/15 bg-night/60 p-space-md text-white shadow-sheet backdrop-blur-md"
    :aria-label="title"
  >
    <header class="flex items-start gap-space-sm">
      <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/15" aria-hidden="true">
        <MsIcon :name="icon" :size="22" />
      </span>
      <div class="min-w-0 flex-1">
        <p class="truncate font-archival text-archival uppercase text-white/70">{{ kicker }}</p>
        <h3 class="font-headline-sm text-headline-sm text-white">{{ title }}</h3>
      </div>
      <button
        type="button"
        aria-label="Закрыть карточку"
        class="-mr-1 -mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white/75 transition-colors hover:bg-white/10 hover:text-white"
        @click="$emit('close')"
      >
        <MsIcon name="close" :size="22" />
      </button>
    </header>

    <ul
      v-if="facts?.length || (fromMe && state === 'idle')"
      class="flex flex-wrap gap-x-space-sm gap-y-1 font-label-md text-label-md text-white/75"
    >
      <li v-if="fromMe && state === 'idle'" class="inline-flex items-center gap-1">
        <MsIcon name="near_me" :size="15" />
        {{ fromMe }} от вас
      </li>
      <li v-for="fact in facts" :key="fact.text" class="inline-flex min-w-0 items-center gap-1">
        <MsIcon :name="fact.icon" :size="15" class="shrink-0" />
        <span class="truncate">{{ fact.text }}</span>
      </li>
    </ul>

    <template v-if="description">
      <p class="font-body-sm text-body-sm text-white/80" :class="{ 'line-clamp-3': !expanded }">{{ description }}</p>
      <button
        v-if="description.length > LONG_DESCRIPTION"
        type="button"
        class="-mt-1 self-start font-label-md text-label-md text-white underline underline-offset-2"
        @click="expanded = !expanded"
      >
        {{ expanded ? 'Свернуть' : 'Читать дальше' }}
      </button>
    </template>

    <button
      v-if="state === 'idle'"
      type="button"
      class="flex h-11 items-center justify-center gap-space-xs rounded-full bg-primary-container font-label-lg text-label-lg text-white shadow-stamp transition-colors hover:bg-primary active:scale-[0.98]"
      @click="start"
    >
      <MsIcon name="route" :size="18" />
      Начать маршрут
    </button>

    <template v-else>
      <div class="flex items-start gap-space-sm rounded-xl bg-white/10 px-space-sm py-2" role="status">
        <MsIcon
          :name="
            state === 'arrived'
              ? 'where_to_vote'
              : state === 'denied'
                ? 'location_off'
                : state === 'active'
                  ? route?.mode === 'car'
                    ? 'directions_car'
                    : 'directions_walk'
                  : 'progress_activity'
          "
          :size="20"
          class="mt-0.5 shrink-0"
          :class="{ 'animate-spin': state === 'locating' || state === 'routing', 'text-tertiary-fixed-dim': state === 'arrived' }"
        />
        <div class="min-w-0 flex-1">
          <p class="font-label-lg text-label-lg text-white">
            <template v-if="state === 'arrived'">Вы на месте</template>
            <template v-else-if="state === 'active'">{{ summary }}</template>
            <template v-else-if="state === 'routing'">Строю маршрут…</template>
            <template v-else-if="state === 'denied'">Нет доступа к геолокации</template>
            <template v-else>Определяю, где вы…</template>
          </p>
          <p v-if="problem" class="font-body-sm text-body-sm text-primary-fixed-dim">{{ problem }}</p>
          <p v-else-if="state === 'active' && route?.estimated" class="font-body-sm text-body-sm text-white/70">
            Сервис маршрутов не ответил — показано направление по прямой
          </p>
        </div>
      </div>

      <div class="flex gap-space-xs">
        <button
          v-if="state === 'denied'"
          type="button"
          class="flex h-11 flex-1 items-center justify-center gap-space-xs rounded-full bg-primary-container font-label-lg text-label-lg text-white shadow-stamp transition-colors hover:bg-primary active:scale-[0.98]"
          @click="start"
        >
          <MsIcon name="refresh" :size="18" />
          Повторить
        </button>
        <button
          v-else-if="state === 'active'"
          type="button"
          class="flex h-11 flex-1 items-center justify-center gap-space-xs rounded-full bg-primary-container font-label-lg text-label-lg text-white shadow-stamp transition-colors hover:bg-primary active:scale-[0.98]"
          @click="openNavigator"
        >
          <MsIcon name="navigation" :size="18" />
          Яндекс Карты
        </button>
        <button
          type="button"
          class="flex h-11 flex-1 items-center justify-center gap-space-xs rounded-full border border-white/20 bg-white/10 font-label-lg text-label-lg text-white backdrop-blur-sm transition-colors hover:bg-white/20 active:scale-[0.98]"
          @click="routing.stop()"
        >
          <MsIcon name="close" :size="18" />
          {{ state === 'arrived' ? 'Готово' : 'Завершить' }}
        </button>
      </div>
    </template>

    <slot />
  </section>
</template>
