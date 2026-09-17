<script setup>
defineProps({
  label: { type: String, default: 'Синтез мимики LivePortrait v2.4' },
  note: { type: String, default: 'Калибровано по фронтовым снимкам 1940 г.' },
  status: { type: String, default: 'Стабильно' },
})
</script>

<template>
  <div class="bg-surface-container-lowest rounded-DEFAULT p-4 shadow-sm flex flex-col gap-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container">
          <span class="material-symbols-outlined text-[20px]">psychology</span>
        </div>
        <div class="flex flex-col">
          <span class="font-label-md text-label-md text-on-surface font-bold">{{ label }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ note }}</span>
        </div>
      </div>
      <span class="px-2.5 py-1 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-label-sm font-bold shrink-0">
        {{ status }}
      </span>
    </div>
    <p class="font-body-sm text-body-sm text-on-surface-variant pl-[3.25rem] -mt-1">
      Заявку на новое «живое фото» можно отправить прямо здесь (ниже) — очередь ставит
      <code class="font-mono">media_service</code>, сам рендер выполняет ещё не подключённый воркер
    </p>
  </div>
</template>
