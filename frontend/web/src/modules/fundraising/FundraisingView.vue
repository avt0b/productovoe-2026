<script setup>
import FundraisingSection from './components/FundraisingSection.vue'
import GroupExcursionRequests from './components/GroupExcursionRequests.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-8">
    <div class="pt-6">
      <h1 class="font-headline-xl text-headline-xl text-on-surface tracking-tight">Сборы и заявки</h1>
      <p class="font-body-lg text-body-lg text-on-surface-variant mt-1">
        Прямая поддержка поисковых отрядов и организация экскурсий для школ и клубов
      </p>
    </div>

    <FundraisingSection />
    <GroupExcursionRequests />
  </div>
</template>
