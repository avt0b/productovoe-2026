<script setup>
import SquadRegisterForm from './components/SquadRegisterForm.vue'
import SchoolRegisterForm from './components/SchoolRegisterForm.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-8">
    <div class="pt-6">
      <h1 class="font-headline-xl text-headline-xl text-on-surface tracking-tight">Регистрация отряда и школы</h1>
      <p class="font-body-lg text-body-lg text-on-surface-variant mt-1">
        Поисковый отряд встаёт на учёт в штабе, школа или клуб — оставляет контакты для будущих
        совместных экскурсий
      </p>
    </div>

    <SquadRegisterForm />
    <SchoolRegisterForm />
  </div>
</template>
