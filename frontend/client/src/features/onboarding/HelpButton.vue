<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import MsIcon from '@/ui/MsIcon.vue'

/**
 * «?» рядом с заголовком экрана — короткий путь в шпаргалку по разделам.
 *
 * Модуля обучения может не быть в сборке: тогда кнопки нет вовсе. Кнопка,
 * которая никуда не ведёт, хуже её отсутствия.
 */
const router = useRouter()

const available = computed(() => router.hasRoute('onboarding'))

function open(): void {
  void router.push({ name: 'onboarding' })
}
</script>

<template>
  <button
    v-if="available"
    type="button"
    aria-label="Как всё устроено"
    class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high active:scale-95"
    @click="open"
  >
    <MsIcon name="help" :size="22" />
  </button>
</template>
