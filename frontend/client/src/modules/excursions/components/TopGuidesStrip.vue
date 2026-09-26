<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { plural } from '@/core/format'
import { fetchLeaderboard, formatRating, PersonAvatar, StarRow, type GuideRank } from '@/features/guide-rating'
import MsIcon from '@/ui/MsIcon.vue'

/**
 * Полоска «Лучшие краеведы» на главном экране экскурсий. Ошибка или пустой
 * рейтинг — блока нет вовсе: не захламляем главный экран. Нет модуля рейтинга —
 * тоже нет.
 */
const router = useRouter()
const enabled = router.hasRoute('guides')

const items = ref<GuideRank[]>([])
const loading = ref(true)
const failed = ref(false)

onMounted(async () => {
  if (!enabled) return
  try {
    const board = await fetchLeaderboard('all', { limit: 5 })
    items.value = board.items
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section v-if="enabled && (loading || (!failed && items.length))" class="flex flex-col gap-space-sm">
    <h3 class="font-headline-sm text-headline-sm text-on-surface">Лучшие краеведы</h3>
    <div class="-mx-margin flex snap-x gap-space-sm overflow-x-auto px-margin pb-1">
      <!-- Загрузка — три серые заглушки. -->
      <template v-if="loading">
        <div v-for="i in 3" :key="i" class="h-36 w-36 shrink-0 animate-pulse snap-start rounded-2xl bg-surface-container" />
      </template>
      <template v-else>
        <RouterLink
          v-for="guide in items"
          :key="guide.guide_id"
          :to="{ name: 'guide', params: { guideId: guide.guide_id } }"
          class="flex w-36 shrink-0 snap-start flex-col items-center gap-1 rounded-2xl bg-surface-container-lowest p-space-sm text-center shadow-document"
        >
          <PersonAvatar :name="guide.display_name" :url="guide.avatar_url" :size="52" />
          <span class="w-full truncate font-label-md text-label-md text-on-surface">{{ guide.display_name }}</span>
          <StarRow :value="guide.average" :size="13" />
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ formatRating(guide.average) }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ guide.count }} {{ plural(guide.count, ['отзыв', 'отзыва', 'отзывов']) }}</span>
        </RouterLink>
        <RouterLink
          :to="{ name: 'guides' }"
          class="flex w-36 shrink-0 snap-start flex-col items-center justify-center gap-space-xs rounded-2xl bg-surface-container p-space-sm text-center"
        >
          <MsIcon name="emoji_events" :size="28" class="text-tertiary" />
          <span class="font-label-md text-label-md text-on-surface">Весь рейтинг</span>
          <MsIcon name="chevron_right" :size="18" class="text-on-surface-variant" />
        </RouterLink>
      </template>
    </div>
  </section>
</template>
