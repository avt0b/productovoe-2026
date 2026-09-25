<script setup>
import SquadRegisterForm from './components/SquadRegisterForm.vue'
import SchoolExcursionRequestForm from './components/SchoolExcursionRequestForm.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-8">
    <div class="pt-6">
      <h1 class="font-headline-xl text-headline-xl text-on-surface tracking-tight">Отряды и заявки школ</h1>
      <p class="font-body-lg text-body-lg text-on-surface-variant mt-1">
        Поисковый отряд встаёт на учёт в штабе, школа или клуб — подаёт заявку на экскурсию
        с гидом-поисковиком или краеведом
      </p>
    </div>

    <SquadRegisterForm />
    <SchoolExcursionRequestForm />
  </div>
</template>
