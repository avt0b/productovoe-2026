<script setup>
import PageHeader from './components/PageHeader.vue'
import HeroPortraitPlayer from './components/HeroPortraitPlayer.vue'
import CalibrationStatus from './components/CalibrationStatus.vue'
import EthicsNotice from './components/EthicsNotice.vue'
import SoldierBio from './components/SoldierBio.vue'
import QuickActions from './components/QuickActions.vue'
import FamilyRelics from './components/FamilyRelics.vue'
import CommunityArchive from './components/CommunityArchive.vue'
import LiveMemorialStudio from './components/LiveMemorialStudio.vue'
</script>

<template>
  <div class="flex flex-col w-full pb-16">
    <PageHeader />

    <div class="grid grid-cols-12 gap-8 items-start">
      <div class="col-span-12 lg:col-span-5 xl:col-span-5 flex flex-col gap-4 sticky top-20">
        <HeroPortraitPlayer />
        <CalibrationStatus />
      </div>

      <div class="col-span-12 lg:col-span-7 xl:col-span-7 flex flex-col gap-6">
        <EthicsNotice />
        <SoldierBio />
        <QuickActions />
        <FamilyRelics />
        <CommunityArchive />
        <LiveMemorialStudio />
      </div>
    </div>
  </div>
</template>
