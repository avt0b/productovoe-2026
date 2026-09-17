<script setup>
import HqHero from './components/HqHero.vue'
import OperationalMetrics from './components/OperationalMetrics.vue'
import FieldPhotoBanner from './components/FieldPhotoBanner.vue'
import FundraisingPromo from './components/FundraisingPromo.vue'
import FieldSchoolCard from './components/FieldSchoolCard.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16">
    <HqHero />

    <div class="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
      <div class="xl:col-span-8 flex flex-col gap-8">
        <OperationalMetrics />
        <FieldPhotoBanner />
        <FundraisingPromo />
      </div>

      <div class="xl:col-span-4 w-full">
        <FieldSchoolCard />
      </div>
    </div>
  </div>
</template>
