<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import MsIcon from './MsIcon.vue'
import UserAvatar from './UserAvatar.vue'

const route = useRoute()
const router = useRouter()

/**
 * Вход в экран NFC-меток, пока он ни к чему не прикручен. Модуль убрали —
 * кнопка пропала сама.
 */
const hasNfc = computed(() => router.hasRoute('nfc'))
</script>

<template>
  <header
    class="pt-safe fixed inset-x-0 top-0 z-50 mx-auto w-full max-w-app bg-surface/80 shadow-header backdrop-blur-xl"
  >
    <div class="flex h-16 items-center justify-between px-margin">
      <div class="flex min-w-0 items-center gap-space-sm">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-fixed text-primary">
          <MsIcon name="explore" :size="20" />
        </div>
        <div class="min-w-0">
          <span class="block font-label-sm text-label-sm uppercase leading-tight tracking-wider text-outline">
            Маршруты победы
          </span>
          <h1 class="truncate font-headline-sm text-headline-sm leading-tight text-on-surface">
            {{ route.meta.title }}
          </h1>
        </div>
      </div>

      <div class="flex items-center gap-space-xs">
        <RouterLink
          v-if="hasNfc"
          :to="{ name: 'nfc' }"
          aria-label="NFC-метка"
          class="flex h-11 w-11 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:text-on-surface"
        >
          <MsIcon name="nfc" :size="22" />
        </RouterLink>
        <button
          type="button"
          aria-label="Поиск"
          class="flex h-11 w-11 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:text-on-surface"
        >
          <MsIcon name="search" :size="22" />
        </button>
        <UserAvatar />
      </div>
    </div>
  </header>
</template>
