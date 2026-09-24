<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

import MsIcon from '@/ui/MsIcon.vue'

import { useNotificationWatcher } from './useNotificationWatcher'

/**
 * Всплывающее уведомление поверх любого экрана.
 *
 * Живёт в корне приложения: сбор начинается, пока человек смотрит карту или
 * профиль, а не экран экскурсии. Одно за раз — если краевед открыл сбор, это
 * главное, что сейчас стоит знать.
 */
const route = useRoute()
const router = useRouter()
const { current, settle } = useNotificationWatcher()

function open(): void {
  const item = current.value
  if (!item) return
  settle()
  // Человек уже на нужном экране — вести некуда, просто убираем плашку.
  const resolved = router.resolve(item.target)
  if (resolved.fullPath !== route.fullPath) void router.push(item.target)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="banner">
      <div
        v-if="current"
        class="banner pt-safe"
        role="alert"
        aria-live="assertive"
      >
        <!--
          Светлая карточка, а не тёмная плашка: уведомление всплывает над
          пергаментом, и тёмное пятно там читалось бы дырой в экране. Все
          виды — полевые (сбор, выход группы, находка рядом), отсюда олива.
        -->
        <div
          class="mx-margin mt-space-sm flex items-start gap-space-sm rounded-2xl border border-outline-variant/60 bg-surface-container-lowest p-space-md shadow-sheet"
        >
          <span class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
            <MsIcon :name="current.icon" :size="20" filled />
          </span>
          <div class="flex min-w-0 flex-1 flex-col gap-0.5">
            <p class="font-archival text-archival uppercase text-on-surface-variant">Уведомление</p>
            <p class="font-headline-sm text-headline-sm text-on-surface">{{ current.notification.title }}</p>
            <p class="font-body-sm text-body-sm text-on-surface-variant">{{ current.notification.body }}</p>
            <button
              type="button"
              class="mt-space-xs flex items-center gap-space-xs self-start rounded-full bg-secondary px-space-md py-2 font-label-md text-label-md text-on-secondary active:scale-95"
              @click="open"
            >
              {{ current.actionLabel }}
              <MsIcon name="arrow_forward" :size="18" />
            </button>
          </div>
          <button
            type="button"
            aria-label="Закрыть уведомление"
            class="-mr-1 -mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container"
            @click="settle"
          >
            <MsIcon name="close" :size="18" />
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.banner {
  position: fixed;
  inset: 0 0 auto;
  /* Выше шапки и панели вкладок, ниже полноэкранных окон вроде «Вы вместе!». */
  z-index: 1500;
}

.banner-enter-active {
  transition:
    transform 320ms cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity 200ms ease-out;
}

.banner-leave-active {
  transition:
    transform 220ms ease-in,
    opacity 180ms ease-in;
}

.banner-enter-from,
.banner-leave-to {
  transform: translateY(-110%);
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .banner-enter-active,
  .banner-leave-active {
    transition: opacity 150ms linear;
  }

  .banner-enter-from,
  .banner-leave-to {
    transform: none;
  }
}
</style>
