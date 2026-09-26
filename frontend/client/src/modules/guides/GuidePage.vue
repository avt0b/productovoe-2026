<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { formatDate, formatDateTime, plural } from '@/core/format'
import {
  fetchGuideCard,
  fetchGuideExcursions,
  formatRating,
  placeLabel,
  PersonAvatar,
  StarRow,
  type GuideExcursion,
} from '@/features/guide-rating'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

/** Карточка краеведа: оценка, распределение, ближайшие экскурсии и отзывы. */
const props = defineProps<{ guideId: string }>()

const router = useRouter()
const card = useAsync(() => fetchGuideCard(props.guideId))
// Ошибка со списком экскурсий не должна ронять экран — грузим отдельно и молча.
const excursions = useAsync<GuideExcursion[]>(() =>
  fetchGuideExcursions(props.guideId).catch(() => [] as GuideExcursion[]),
)

const name = computed(() => card.data.value?.profile?.display_name ?? 'Краевед')
const hasRatings = computed(() => (card.data.value?.count ?? 0) > 0)

const bars = computed(() => {
  const c = card.data.value
  if (!c) return []
  const total = Math.max(1, c.count)
  return (['5', '4', '3', '2', '1'] as const).map((star) => ({
    star,
    count: c.distribution[star],
    pct: Math.round((c.distribution[star] / total) * 100),
  }))
})

const upcoming = computed(() => excursions.data.value ?? [])
const hasExcursionRoute = computed(() => router.hasRoute('excursion'))

function openExcursion(id: string): void {
  if (hasExcursionRoute.value) void router.push({ name: 'excursion', params: { excursionId: id } })
}
</script>

<template>
  <div class="flex flex-col gap-space-md px-margin py-space-md">
    <StateBlock :loading="card.loading.value" :error="card.error.value" @retry="card.retry" />

    <template v-if="card.data.value">
      <!-- Шапка. -->
      <div class="flex items-center gap-space-md">
        <PersonAvatar :name="name" :url="card.data.value.profile?.avatar_url ?? null" :size="72" />
        <div class="min-w-0">
          <h2 class="font-headline-md text-headline-md text-on-surface">{{ name }}</h2>
          <p v-if="card.data.value.profile?.city" class="font-body-sm text-body-sm text-on-surface-variant">{{ card.data.value.profile.city }}</p>
          <p v-if="card.data.value.profile?.is_verified" class="mt-1 inline-flex items-center gap-1 font-label-sm text-label-sm text-tertiary">
            <MsIcon name="verified" :size="14" filled /> Подтверждённый краевед
          </p>
        </div>
      </div>

      <!-- Оценка. -->
      <div class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <template v-if="hasRatings">
          <div class="flex items-center gap-space-md">
            <span class="font-headline-lg text-headline-lg text-on-surface">{{ formatRating(card.data.value.average) }}</span>
            <div class="flex flex-col">
              <StarRow :value="card.data.value.average" :size="18" />
              <span class="font-body-sm text-body-sm text-on-surface-variant">{{ card.data.value.count }} {{ plural(card.data.value.count, ['отзыв', 'отзыва', 'отзывов']) }}</span>
            </div>
            <button
              v-if="card.data.value.place"
              type="button"
              class="ml-auto flex items-center gap-1 rounded-full bg-tertiary-fixed px-space-sm py-1 font-label-md text-label-md text-tertiary active:scale-95"
              @click="router.push({ name: 'guides' })"
            >
              {{ placeLabel(card.data.value.place) }} из {{ card.data.value.total_ranked }}
              <MsIcon name="chevron_right" :size="16" />
            </button>
          </div>

          <!-- Распределение оценок. -->
          <div class="flex flex-col gap-1">
            <div v-for="bar in bars" :key="bar.star" class="flex items-center gap-space-sm">
              <span class="w-3 text-right font-body-sm text-body-sm text-on-surface-variant">{{ bar.star }}</span>
              <div class="h-2 flex-1 overflow-hidden rounded-full bg-surface-container">
                <div class="h-full rounded-full bg-tertiary" :style="{ width: `${bar.pct}%` }" />
              </div>
              <span class="w-6 text-right font-body-sm text-body-sm text-on-surface-variant">{{ bar.count }}</span>
            </div>
          </div>
        </template>
        <p v-else class="font-body-md text-body-md text-on-surface-variant">
          Пока без оценок — оценить краеведа можно после экскурсии с ним
        </p>
      </div>

      <p class="font-body-md text-body-md text-on-surface-variant">
        Провёл(а) экскурсий: {{ card.data.value.excursions_led }}
      </p>

      <!-- Ближайшие экскурсии. -->
      <section v-if="upcoming.length" class="flex flex-col gap-space-sm">
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Ближайшие экскурсии</h3>
        <button
          v-for="exc in upcoming"
          :key="exc.id"
          type="button"
          class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-sm text-left shadow-document"
          @click="openExcursion(exc.id)"
        >
          <MsIcon name="hiking" :size="20" class="shrink-0 text-tertiary" />
          <div class="min-w-0 flex-1">
            <p class="truncate font-label-lg text-label-lg text-on-surface">{{ exc.title }}</p>
            <p class="font-body-sm text-body-sm text-on-surface-variant">{{ formatDateTime(exc.starts_at) }} · {{ exc.place_name }}</p>
          </div>
          <MsIcon v-if="hasExcursionRoute" name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
        </button>
      </section>

      <!-- Отзывы. -->
      <section v-if="card.data.value.recent.length" class="flex flex-col gap-space-sm">
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Отзывы</h3>
        <article
          v-for="review in card.data.value.recent"
          :key="review.id"
          class="flex flex-col gap-space-xs rounded-2xl bg-surface-container-lowest p-space-sm shadow-document"
        >
          <div class="flex items-center gap-space-sm">
            <PersonAvatar :name="review.rater_name" :url="review.rater_avatar_url" :size="36" />
            <div class="min-w-0 flex-1">
              <p class="truncate font-label-md text-label-md text-on-surface">{{ review.rater_name }}</p>
              <StarRow :value="review.rating" :size="12" />
            </div>
            <span class="shrink-0 font-body-sm text-body-sm text-on-surface-variant">{{ formatDate(review.created_at) }}</span>
          </div>
          <p class="font-body-sm text-body-sm text-on-surface-variant">{{ review.excursion_title }}</p>
          <p v-if="review.comment" class="font-body-md text-body-md text-on-surface">{{ review.comment }}</p>
        </article>
      </section>
    </template>
  </div>
</template>
