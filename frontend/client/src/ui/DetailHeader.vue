<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { shareCurrentPage } from '@/core/share'

import MsIcon from './MsIcon.vue'
import UserAvatar from './UserAvatar.vue'

const route = useRoute()
const router = useRouter()

/**
 * Системного окна отправки в Android WebView нет — ссылка уходит в буфер.
 * Без отметки на кнопке нажатие выглядит как «ничего не произошло».
 */
const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

async function share(): Promise<void> {
  const outcome = await shareCurrentPage(route.meta.title)
  if (outcome !== 'copied') return
  copied.value = true
  clearTimeout(copiedTimer)
  copiedTimer = setTimeout(() => (copied.value = false), 2000)
}

onBeforeUnmount(() => clearTimeout(copiedTimer))

/** Открыли карточку по прямой ссылке — «назад» некуда, ведём на стартовый экран. */
function goBack(): void {
  if (window.history.state?.back) router.back()
  else void router.push({ name: 'home' })
}
</script>

<template>
  <header
    class="pt-safe fixed inset-x-0 top-0 z-50 mx-auto w-full max-w-app bg-surface/80 shadow-header backdrop-blur-xl"
  >
    <div class="flex h-16 items-center justify-between px-margin">
      <div class="flex min-w-0 items-center gap-space-sm">
        <button
          type="button"
          aria-label="Назад"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-on-surface transition-colors hover:bg-surface-container-high"
          @click="goBack"
        >
          <MsIcon name="arrow_back" />
        </button>
        <h1 class="max-w-52 truncate font-headline-sm text-headline-sm text-on-surface">
          {{ route.meta.title }}
        </h1>
      </div>

      <div class="flex items-center gap-space-xs">
        <button
          type="button"
          :aria-label="copied ? 'Ссылка скопирована' : 'Поделиться'"
          class="flex h-11 w-11 items-center justify-center rounded-full transition-colors"
          :class="copied ? 'text-secondary' : 'text-on-surface-variant hover:text-on-surface'"
          @click="share"
        >
          <MsIcon :name="copied ? 'check' : 'share'" :size="22" />
        </button>
        <UserAvatar />
      </div>
    </div>
  </header>
</template>
