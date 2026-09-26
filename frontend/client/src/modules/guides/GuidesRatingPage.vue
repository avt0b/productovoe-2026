<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { errorText, plural } from '@/core/format'
import { fetchLeaderboard, formatRating, PersonAvatar, StarRow, type GuideRank, type RatingPeriod } from '@/features/guide-rating'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SegmentTabs from '@/ui/SegmentTabs.vue'
import StateBlock from '@/ui/StateBlock.vue'

/**
 * Таблица краеведов. Место считает бэкенд байесовским средним (CONTRACT 2.2):
 * экран только показывает и объясняет это словами.
 */
const router = useRouter()
const PAGE = 50

const period = ref<RatingPeriod>('all')
const items = ref<GuideRank[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)
const loadingMore = ref(false)
const noticeOpen = ref(false)

const tabs = [
  { value: 'all' as const, title: 'За всё время', icon: 'emoji_events' },
  { value: 'month' as const, title: 'За месяц', icon: 'calendar_month' },
]

async function load(reset: boolean): Promise<void> {
  if (reset) {
    loading.value = true
    error.value = null
    items.value = []
  } else {
    loadingMore.value = true
  }
  try {
    const board = await fetchLeaderboard(period.value, { limit: PAGE, offset: reset ? 0 : items.value.length })
    items.value = reset ? board.items : [...items.value, ...board.items]
    total.value = board.total
  } catch (reason) {
    if (reset) error.value = errorText(reason)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

watch(period, () => void load(true))
void load(true)

const podium = computed(() => items.value.slice(0, 3))
/** Пьедестал: 2-е слева, 1-е по центру, 3-е справа. */
const podiumOrder = computed(() => [podium.value[1], podium.value[0], podium.value[2]].filter(Boolean) as GuideRank[])
const rest = computed(() => items.value.slice(3))
const canLoadMore = computed(() => items.value.length < total.value)

const placeTone: Record<number, string> = { 1: 'text-tertiary', 2: 'text-on-surface-variant', 3: 'text-primary' }

function reviewsWord(count: number): string {
  return `${count} ${plural(count, ['отзыв', 'отзыва', 'отзывов'])}`
}
function open(guide: GuideRank): void {
  void router.push({ name: 'guide', params: { guideId: guide.guide_id } })
}
</script>

<template>
  <div class="flex flex-col gap-space-md px-margin py-space-md">
    <SegmentTabs v-model="period" :tabs="tabs" label="Период рейтинга" id-prefix="guides-period" />

    <button
      type="button"
      class="text-left"
      @click="noticeOpen = !noticeOpen"
    >
      <InlineNotice tone="info" icon="info">
        <span class="font-label-md text-label-md">Как считаем места</span>
        <p v-if="noticeOpen" class="mt-1 font-body-sm text-body-sm">
          Место зависит и от оценки, и от числа отзывов: одна пятёрка не обгонит сорок оценок по 4,8.
          Считаем только оценки тех, кто действительно был на экскурсии.
        </p>
      </InlineNotice>
    </button>

    <StateBlock
      :loading="loading"
      :error="error"
      :empty="!loading && !error && items.length === 0"
      empty-icon="emoji_events"
      empty-text="Пока никто не оценил краеведов — оценки появятся после первых экскурсий"
      @retry="load(true)"
    />

    <template v-if="!loading && !error && items.length">
      <!-- Пьедестал: первые три. -->
      <div class="grid grid-cols-3 items-end gap-space-xs">
        <button
          v-for="guide in podiumOrder"
          :key="guide.guide_id"
          type="button"
          class="flex flex-col items-center gap-1 rounded-2xl bg-surface-container-lowest p-space-sm shadow-document"
          :class="{ '-translate-y-2': guide.place === 1 }"
          @click="open(guide)"
        >
          <span class="font-headline-sm text-headline-sm" :class="placeTone[guide.place] ?? 'text-on-surface-variant'">{{ guide.place }}</span>
          <PersonAvatar :name="guide.display_name" :url="guide.avatar_url" :size="guide.place === 1 ? 64 : 52" />
          <span class="line-clamp-2 text-center font-label-md text-label-md text-on-surface">{{ guide.display_name }}</span>
          <StarRow :value="guide.average" :size="14" />
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ formatRating(guide.average) }} · {{ reviewsWord(guide.count) }}</span>
        </button>
      </div>

      <!-- Остальные — строками. -->
      <ul class="flex flex-col gap-space-xs">
        <li
          v-for="guide in rest"
          :key="guide.guide_id"
        >
          <button
            type="button"
            class="flex w-full items-center gap-space-sm rounded-2xl p-space-sm text-left shadow-document"
            :class="guide.is_me ? 'bg-secondary-container' : 'bg-surface-container-lowest'"
            @click="open(guide)"
          >
            <span class="w-6 shrink-0 text-center font-headline-sm text-headline-sm text-on-surface-variant">{{ guide.place }}</span>
            <PersonAvatar :name="guide.display_name" :url="guide.avatar_url" :size="44" />
            <div class="min-w-0 flex-1">
              <p class="flex items-center gap-1 font-label-lg text-label-lg text-on-surface">
                <span class="truncate">{{ guide.display_name }}</span>
                <MsIcon v-if="guide.is_verified" name="verified" :size="16" filled class="shrink-0 text-tertiary" />
                <span v-if="guide.is_me" class="shrink-0 rounded-full bg-secondary px-2 py-0.5 font-label-sm text-label-sm text-on-secondary">Это вы</span>
              </p>
              <p class="truncate font-body-sm text-body-sm text-on-surface-variant">{{ guide.city }}</p>
              <p class="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
                <StarRow :value="guide.average" :size="12" />
                {{ formatRating(guide.average) }} · {{ reviewsWord(guide.count) }} · {{ guide.excursions_led }} {{ plural(guide.excursions_led, ['экскурсия', 'экскурсии', 'экскурсий']) }}
              </p>
            </div>
            <MsIcon name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
          </button>
        </li>
      </ul>

      <button
        v-if="canLoadMore"
        type="button"
        class="mx-auto flex items-center gap-space-xs rounded-full bg-surface-container px-space-lg py-space-sm font-label-lg text-label-lg text-on-surface active:scale-95 disabled:opacity-60"
        :disabled="loadingMore"
        @click="load(false)"
      >
        <MsIcon v-if="loadingMore" name="progress_activity" :size="18" class="animate-spin" />
        Показать ещё
      </button>
    </template>
  </div>
</template>
