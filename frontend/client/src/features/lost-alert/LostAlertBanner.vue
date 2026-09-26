<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { formatDistance } from '@/core/geo'
import { usePreferencesStore } from '@/core/preferences'
import MsIcon from '@/ui/MsIcon.vue'

import { useActiveLostAlerts } from './useActiveLostAlerts'

/**
 * Красная плашка тревоги поверх любого экрана. Живёт в корне приложения:
 * человек мог уйти с карты поиска на профиль — плашка вернёт его назад.
 * Ниже [NotificationBanner] по z: спокойное уведомление не должно перекрывать
 * тревогу, но и тревога не должна прятать критическое системное сообщение.
 */
const route = useRoute()
const router = useRouter()
const preferences = usePreferencesStore()
const { alerts } = useActiveLostAlerts()

/** Тревоги, кроме той, чей экран сейчас открыт, — новые первыми. */
const pending = computed(() =>
  alerts.value
    .filter((a) => !(route.name === 'lost-alert' && route.params.alertId === a.id))
    .slice()
    .sort((a, b) => b.created_at.localeCompare(a.created_at)),
)

const top = computed(() => pending.value[0] ?? null)
const extra = computed(() => Math.max(0, pending.value.length - 1))

const label = computed(() => {
  const alert = top.value
  if (!alert) return ''
  if (alert.my_role === 'lost') return preferences.familyMode ? 'Тебя ищут — открой карту' : 'Вас ищут — откройте карту'
  const me = alert.watchers.find((w) => w.is_me)
  const distance = me && me.distance_m != null ? ` · ${formatDistance(me.distance_m / 1000)}` : ''
  return `Идёт поиск: «${alert.lost.display_name}»${distance}`
})

function open(): void {
  const alert = top.value
  if (!alert || !router.hasRoute('lost-alert')) return
  void router.push({ name: 'lost-alert', params: { alertId: alert.id } })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="lost-banner">
      <button
        v-if="top"
        type="button"
        class="lost-banner pt-safe"
        role="alert"
        aria-live="assertive"
        @click="open"
      >
        <div class="mx-margin mt-space-sm flex items-center gap-space-sm rounded-2xl bg-error p-space-md text-on-error shadow-sheet">
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-on-error/15">
            <MsIcon name="sos" :size="20" filled />
          </span>
          <span class="min-w-0 flex-1 truncate text-left font-headline-sm text-headline-sm">{{ label }}</span>
          <span
            v-if="extra > 0"
            class="shrink-0 rounded-full bg-on-error/15 px-space-sm py-0.5 font-label-md text-label-md"
          >+{{ extra }}</span>
          <MsIcon name="chevron_right" :size="22" class="shrink-0" />
        </div>
      </button>
    </Transition>
  </Teleport>
</template>

<style scoped>
.lost-banner {
  position: fixed;
  inset: 0 0 auto;
  width: 100%;
  /* Ниже NotificationBanner (1500), но выше шапки, вкладок и контента. */
  z-index: 1400;
}

.lost-banner-enter-active {
  transition:
    transform 320ms cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity 200ms ease-out;
}

.lost-banner-leave-active {
  transition:
    transform 220ms ease-in,
    opacity 180ms ease-in;
}

.lost-banner-enter-from,
.lost-banner-leave-to {
  transform: translateY(-110%);
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .lost-banner-enter-active,
  .lost-banner-leave-active {
    transition: opacity 150ms linear;
  }

  .lost-banner-enter-from,
  .lost-banner-leave-to {
    transform: none;
  }
}
</style>
