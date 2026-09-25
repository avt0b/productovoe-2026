<script setup lang="ts">
import MsIcon from './MsIcon.vue'

/**
 * Плашка «показаны демо-данные».
 *
 * Ставится, когда сервис не ответил и экран взял встроенный набор
 * (`withDemoFallback`). Без неё демо легко принять за живые данные.
 */
</script>

<template>
  <p
    class="flex items-start gap-space-sm rounded-DEFAULT bg-tertiary-fixed/50 px-space-sm py-2 font-body-sm text-body-sm text-on-tertiary-fixed-variant"
    role="status"
  >
    <MsIcon name="cloud_off" :size="18" class="mt-0.5 shrink-0" />
    <span><slot>Нет связи с сервером — показаны демо-данные</slot></span>
  </p>
</template>
