<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { plural } from '@/core/format'
import { useSessionStore } from '@/core/session'
import { fetchGuideCard, formatRating, placeLabel, StarRow, type GuideCard } from '@/features/guide-rating'
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Блок рейтинга в профиле краеведа: своя оценка и место. Ошибка — карточки
 * просто нет (профиль от этого не ломается).
 */
const session = useSessionStore()
const router = useRouter()
const card = ref<GuideCard | null>(null)
const failed = ref(false)

onMounted(async () => {
  const id = session.user?.id
  if (!id) return
  try {
    card.value = await fetchGuideCard(id)
  } catch {
    failed.value = true
  }
})
</script>

<template>
  <section v-if="card && !failed" class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <p class="font-archival text-archival uppercase text-on-surface-variant">Ваш рейтинг</p>

    <template v-if="card.count > 0">
      <div class="flex items-center gap-space-md">
        <span class="font-headline-lg text-headline-lg text-on-surface">{{ formatRating(card.average) }}</span>
        <div class="flex flex-col">
          <StarRow :value="card.average" :size="16" />
          <span class="font-body-sm text-body-sm text-on-surface-variant">
            <template v-if="card.place">{{ placeLabel(card.place) }} из {{ card.total_ranked }} · </template>{{ card.count }} {{ plural(card.count, ['отзыв', 'отзыва', 'отзывов']) }}
          </span>
        </div>
      </div>
      <RouterLink
        v-if="router.hasRoute('guide')"
        :to="{ name: 'guide', params: { guideId: card.guide_id } }"
        class="inline-flex items-center gap-1 self-start rounded-full bg-surface-container px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
      >
        Моя карточка
        <MsIcon name="chevron_right" :size="16" />
      </RouterLink>
    </template>
    <p v-else class="font-body-md text-body-md text-on-surface-variant">
      Пока нет оценок — проведите экскурсию, и участники смогут вас оценить
    </p>
  </section>
</template>
