<script setup>
defineProps({
  label: { type: String, default: 'Доступно в приложении' },
  size: { type: String, default: 'sm' },
})
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm font-bold whitespace-nowrap"
    :class="size === 'sm' ? 'px-2 py-0.5 text-label-sm' : 'px-2.5 py-1 text-label-md'"
    title="Эта функция работает только в мобильном приложении «Маршруты победы»"
  >
    <span class="material-symbols-outlined text-[14px]">smartphone</span>
    {{ label }}
  </span>
</template>
