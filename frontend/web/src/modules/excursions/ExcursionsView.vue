<script setup>
import ExcursionSignupForm from './components/ExcursionSignupForm.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-8">
    <div class="pt-6">
      <h1 class="font-headline-xl text-headline-xl text-on-surface tracking-tight">Запись на экскурсии</h1>
      <p class="font-body-lg text-body-lg text-on-surface-variant mt-1">
        Школы, клубы и просто желающие записываются на экскурсии с гидами-поисковиками и краеведами
      </p>
    </div>

    <ExcursionSignupForm />
  </div>
</template>
