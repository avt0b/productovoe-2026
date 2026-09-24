<script setup>
import CommunityArchive from './components/CommunityArchive.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-6 max-w-3xl mx-auto">
    <div class="bg-surface-container-lowest rounded-2xl shadow-document p-6 flex flex-col gap-1">
      <span class="font-archival text-archival uppercase text-tertiary">Модуль 6 ТЗ</span>
      <h1 class="font-headline-lg text-headline-lg text-on-surface font-bold">Живая память</h1>
      <p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">
        Народный архив: малоизвестные подвиги, локальные события и карточки бойцов, не попавшие в
        федеральные базы. Любой может предложить запись — поисковик, краевед, наставник или модератор
        подтверждает её (archive_service).
      </p>
    </div>

    <CommunityArchive />
  </div>
</template>
