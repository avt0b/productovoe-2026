<script setup>
import ProfileHero from './components/ProfileHero.vue'
import ProfileMetrics from './components/ProfileMetrics.vue'
import FamilyTree from './components/FamilyTree.vue'
import AwardsBadges from './components/AwardsBadges.vue'
import ResearcherDataForm from './components/ResearcherDataForm.vue'
import ExpeditionSettings from './components/ExpeditionSettings.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16">
    <ProfileHero />
    <ProfileMetrics />

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <div class="lg:col-span-7 flex flex-col gap-8">
        <FamilyTree />
        <AwardsBadges />
      </div>

      <div class="lg:col-span-5 flex flex-col gap-8">
        <ResearcherDataForm />
        <ExpeditionSettings />
      </div>
    </div>
  </div>
</template>
