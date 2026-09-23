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
        <div class="mx-space-sm mt-space-sm flex items-start gap-space-sm rounded-lg bg-inverse-surface p-space-md text-inverse-on-surface shadow-lg">
          <span class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-on-primary">
            <MsIcon name="campaign" :size="20" filled />
          </span>
          <div class="flex min-w-0 flex-1 flex-col gap-0.5">
            <p class="font-headline-sm text-headline-sm">{{ current.notification.title }}</p>
            <p class="font-body-sm text-body-sm opacity-80">{{ current.notification.body }}</p>
            <button
              type="button"
              class="mt-space-xs self-start rounded-full bg-primary px-space-md py-1.5 font-label-lg text-label-lg text-on-primary active:scale-95"
              @click="open"
            >
              {{ current.actionLabel }}
            </button>
          </div>
          <button
            type="button"
            aria-label="Закрыть уведомление"
            class="-mr-1 -mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full opacity-70 hover:opacity-100"
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
