<script setup>
import EthicsNotice from './components/EthicsNotice.vue'
import LiveMemorialStudio from './components/LiveMemorialStudio.vue'
import MemorialGallery from './components/MemorialGallery.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-6">
    <div class="bg-surface-container-lowest rounded-2xl shadow-document p-6 flex flex-col gap-1">
      <span class="font-archival text-archival uppercase text-tertiary">Модуль 7 ТЗ</span>
      <h1 class="font-headline-lg text-headline-lg text-on-surface font-bold">Живое фото</h1>
      <p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">
        Загрузите фотографию бойца — media_render_worker озвучит текст через Yandex SpeechKit и оживит
        снимок под голос через Replicate (SadTalker). Готовый ролик можно отправить родным или добавить
        в общий мемориал платформы.
      </p>
    </div>

    <EthicsNotice />
    <LiveMemorialStudio />
    <MemorialGallery />
  </div>
</template>
