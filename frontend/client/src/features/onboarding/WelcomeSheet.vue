<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSessionStore } from '@/core/session'
import Mascot from '@/ui/Mascot.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'

import { markSeen, needsWelcome } from './state'

/**
 * Первое знакомство: одно предложение помочь разобраться — и больше никогда.
 *
 * Разделов пять, в каждом свои сценарии, и без подсказки человек находит от
 * силы два. Но обучение, которое навязывается, закрывают не читая, поэтому
 * здесь только приглашение: показать или нет — решает человек, а ответ
 * запоминается в любом случае (`features/onboarding/state`).
 */
const session = useSessionStore()
const route = useRoute()
const router = useRouter()

/** Обучение живёт в своём модуле — его может не быть в сборке. */
const hasTour = computed(() => router.hasRoute('onboarding'))

const open = computed(
  () =>
    hasTour.value &&
    needsWelcome.value &&
    session.isAuthenticated &&
    // На входе и на самом обучении здороваться не с кем; на полноэкранных
    // картах (группа идёт, AR) окно поверх — помеха, а не помощь.
    route.name !== 'onboarding' &&
    route.meta.auth !== true &&
    route.meta.layout !== 'bare',
)

function show(): void {
  markSeen()
  void router.push({ name: 'onboarding', query: { tour: '1' } })
}

function later(): void {
  markSeen()
}
</script>

<template>
  <SheetDialog
    v-if="open"
    title="Показать, что здесь где?"
    subtitle="Минута — и понятно, чем занят каждый раздел"
    @close="later"
  >
    <div class="flex flex-col gap-space-md pb-space-sm">
      <div class="flex items-center gap-space-sm rounded-2xl bg-surface-container-low p-space-md">
        <Mascot pose="wave" :size="112" class="-my-space-sm" />
        <p class="font-body-md text-body-md text-on-surface">
          Маршруты по местам боёв, экскурсии с краеведами, народный архив и помощь поисковым отрядам — всё это разные
          разделы. Покажем, где что, и с чего начать именно вам.
        </p>
      </div>

      <button
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="show"
      >
        <MsIcon name="play_arrow" :size="18" />
        <span>Показать</span>
      </button>
      <button
        type="button"
        class="min-h-11 self-center rounded-full px-space-md py-2 font-label-md text-label-md text-on-surface-variant active:scale-95"
        @click="later"
      >
        Разберусь сам
      </button>
      <p class="text-center font-body-sm text-body-sm text-on-surface-variant">
        Обучение останется в профиле — открыть можно в любой момент.
      </p>
    </div>
  </SheetDialog>
</template>
