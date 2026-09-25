<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { distanceKm, formatDistance, type GeoTone, type LatLon } from '@/core/geo'
import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { PLACE_KINDS, type MapPlace } from '../data'

/**
 * Список найденных мест под картой.
 *
 * Карта отвечает на «где это», список — на «что вообще нашлось»: после поиска
 * по слову или по году метки могут оказаться за краем экрана, и без списка
 * человек видит пустую карту и решает, что ничего не найдено.
 *
 * Все места сразу, но в карточке своей высоты: листается внутри, а страница
 * под картой не вытягивается на всю область. Край, за которым есть ещё места,
 * растворяется, а внизу висит подсказка, сколько осталось, — тапнул, и список
 * сам пролистался. Выбрали метку на карте — строка сама выезжает в видимое.
 */
const props = defineProps<{
  places: MapPlace[]
  selectedId: string | null
  /** Где человек, если он разрешил определять место. Знаем — сортируем по близости. */
  user: LatLon | null
}>()

defineEmits<{ select: [id: string] }>()

const TONE_CLASS: Record<GeoTone, string> = {
  primary: 'bg-primary-fixed text-primary',
  secondary: 'bg-secondary-fixed text-secondary',
  tertiary: 'bg-tertiary-fixed text-tertiary',
  neutral: 'bg-surface-container-high text-on-surface-variant',
}

const rows = computed(() => {
  const items = props.places.map((place) => ({
    place,
    km: props.user ? distanceKm(props.user, place) : null,
  }))
  // Знаем, где человек, — ближние вперёд: на прогулке важно, до чего дойти сейчас.
  if (props.user) items.sort((a, b) => (a.km ?? 0) - (b.km ?? 0))
  return items
})

const countLabel = computed(() => `${props.places.length} ${plural(props.places.length, ['место', 'места', 'мест'])}`)

const listEl = ref<HTMLUListElement | null>(null)
/** Листается ли список вообще, у верхнего ли он края, у нижнего ли, и сколько строк ещё ниже. */
const scrollable = ref(false)
const atTop = ref(true)
const atEnd = ref(true)
const below = ref(0)

function measure(): void {
  const el = listEl.value
  if (!el) return
  const bottom = el.scrollTop + el.clientHeight
  scrollable.value = el.scrollHeight > el.clientHeight + 1
  atTop.value = el.scrollTop <= 1
  atEnd.value = bottom >= el.scrollHeight - 1
  // Строка «ниже», если её середина за нижним краем: полстроки видно — её уже заметили.
  let hidden = 0
  for (const item of el.children) {
    const li = item as HTMLElement
    if (li.offsetTop + li.offsetHeight / 2 > bottom) hidden += 1
  }
  below.value = hidden
}

let frame = 0
function onScroll(): void {
  if (frame) return
  frame = requestAnimationFrame(() => {
    frame = 0
    measure()
  })
}

let resizeObserver: ResizeObserver | null = null
onMounted(() => {
  measure()
  if (listEl.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(measure)
    resizeObserver.observe(listEl.value)
  }
})
onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  if (frame) cancelAnimationFrame(frame)
})

function motion(): ScrollBehavior {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
}

// Сменился набор мест (поиск, фильтр, год) — начинаем сверху, со свежего.
watch(
  () => props.places,
  async () => {
    listEl.value?.scrollTo({ top: 0 })
    await nextTick()
    measure()
  },
)
// Человек нашёлся — порядок стал «по близости», пересчитываем, что видно.
watch(rows, () => void nextTick(measure))

// Выбрали метку на карте — строку показываем посреди списка, если её не видно.
watch(
  () => props.selectedId,
  async (id) => {
    if (!id) return
    await nextTick()
    const el = listEl.value
    const li = el ? Array.from(el.children).find((item) => (item as HTMLElement).dataset.id === id) : null
    if (!el || !(li instanceof HTMLElement)) return
    const top = li.offsetTop
    const bottom = top + li.offsetHeight
    if (top >= el.scrollTop && bottom <= el.scrollTop + el.clientHeight) return
    el.scrollTo({ top: top - (el.clientHeight - li.offsetHeight) / 2, behavior: motion() })
  },
)

/** Пролистать на экран списка вниз — по тапу на подсказку «ещё N». */
function scrollOn(): void {
  const el = listEl.value
  el?.scrollBy({ top: el.clientHeight * 0.8, behavior: motion() })
}

/** Край, за которым есть ещё места, растворяется — видно, что список продолжается. */
const fade = computed(() => {
  if (!scrollable.value) return undefined
  const top = atTop.value ? 'black 0' : 'transparent 0, black 1.5rem'
  const bottom = atEnd.value ? 'black 100%' : 'black calc(100% - 3.5rem), transparent 100%'
  const mask = `linear-gradient(to bottom, ${top}, ${bottom})`
  return { maskImage: mask, WebkitMaskImage: mask }
})
</script>

<template>
  <section class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest pt-space-md shadow-document">
    <div class="flex items-center justify-between gap-space-sm px-space-md">
      <h2 class="font-archival text-archival uppercase text-on-surface-variant">Найдено {{ countLabel }}</h2>
      <span v-if="user && places.length > 1" class="flex items-center gap-1 font-label-sm text-label-sm text-on-surface-variant">
        <MsIcon name="near_me" :size="14" class="text-secondary" />
        Ближние сверху
      </span>
    </div>

    <div class="relative">
      <ul
        ref="listEl"
        class="no-scrollbar relative flex max-h-[21.5rem] flex-col gap-1 overflow-y-auto px-space-sm pb-space-sm"
        :style="fade"
        :aria-label="`Найденные места: ${countLabel}`"
        @scroll.passive="onScroll"
      >
        <li v-for="row in rows" :key="row.place.id" :data-id="row.place.id">
          <button
            type="button"
            class="flex w-full items-center gap-space-sm rounded-2xl p-space-sm text-left transition-colors"
            :class="selectedId === row.place.id ? 'bg-secondary-container/60' : 'hover:bg-surface-container-low active:bg-surface-container-low'"
            :aria-pressed="selectedId === row.place.id"
            @click="$emit('select', row.place.id)"
          >
            <span
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
              :class="TONE_CLASS[PLACE_KINDS[row.place.kind].tone]"
            >
              <MsIcon :name="PLACE_KINDS[row.place.kind].icon" :size="18" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-label-lg text-label-lg text-on-surface">{{ row.place.title }}</span>
              <span class="block truncate font-body-sm text-body-sm text-on-surface-variant">
                {{ PLACE_KINDS[row.place.kind].title }}<template v-if="row.place.dateText"> · {{ row.place.dateText }}</template>
              </span>
            </span>
            <span
              v-if="row.km !== null"
              class="shrink-0 font-label-md text-label-md text-outline"
              >{{ formatDistance(row.km) }}</span
            >
          </button>
        </li>
      </ul>

      <!-- Подсказка поверх растворённого края: сколько ещё ниже. Список сам всё скажет и без неё — поэтому aria-hidden. -->
      <Transition
        enter-active-class="transition duration-200 ease-out motion-reduce:transition-none"
        enter-from-class="translate-y-1 opacity-0"
        leave-active-class="transition duration-150 ease-in motion-reduce:transition-none"
        leave-to-class="translate-y-1 opacity-0"
      >
        <button
          v-if="scrollable && !atEnd && below > 0"
          type="button"
          tabindex="-1"
          aria-hidden="true"
          class="absolute bottom-space-sm left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-full bg-surface-container-high py-1 pl-3 pr-2 font-label-md text-label-md text-on-surface shadow-document active:scale-95"
          @click="scrollOn"
        >
          ещё {{ below }}
          <MsIcon name="expand_more" :size="18" />
        </button>
      </Transition>
    </div>
  </section>
</template>
