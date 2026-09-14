<script setup>
import { ref } from 'vue'
import FundraisingCard from './FundraisingCard.vue'
import DonationModal from './DonationModal.vue'

const campaigns = [
  {
    squadName: 'Отряд «Высота»',
    location: 'г. Орёл',
    emblemUrl: 'https://loremflickr.com/96/96/patch?lock=210',
    tag: 'Срочный сбор',
    tagClass: 'bg-surface-container-high text-on-surface-variant',
    title: 'Бензин для мотопомп и дизельный генератор',
    text: 'Откачка грунтовых вод из заболоченных воронок у ручья Озерна. Без помпы невозможно поднять затопленный блиндаж.',
    raised: '35 000 ₽',
    goal: 'из 50 000 ₽',
    percent: 70,
    donors: '142 благотворителя',
    barClass: 'bg-primary',
    raisedTextClass: 'text-primary',
    ctaLabel: 'Помочь отряду (от 100 ₽)',
    ctaClass: 'bg-primary hover:bg-primary/90 text-on-primary shadow-md',
    ctaIcon: 'volunteer_activism',
    ctaIconClass: '',
  },
  {
    squadName: 'Отряд «Рубеж»',
    location: 'г. Болхов',
    emblemUrl: 'https://loremflickr.com/96/96/compass?lock=299',
    tag: 'Оборудование',
    tagClass: 'bg-secondary-container text-on-secondary-container',
    title: 'Глубинное металлодетекторное оборудование',
    text: 'Приобретение импульсного глубинного прибора для локализации засыпанных окопов и тяжелой бронетехники на глубине до 3.5 метров.',
    raised: '78 000 ₽',
    goal: 'из 120 000 ₽',
    percent: 65,
    donors: '89 благотворителей',
    barClass: 'bg-secondary',
    raisedTextClass: 'text-on-surface',
    ctaLabel: 'Поддержать снаряжение',
    ctaClass: 'bg-surface-container hover:bg-surface-container-high text-on-surface',
    ctaIcon: 'handshake',
    ctaIconClass: 'text-secondary',
  },
]

const donationOpen = ref(false)
const selectedCampaign = ref(null)

function openDonation(campaign) {
  selectedCampaign.value = campaign
  donationOpen.value = true
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
      <div>
        <h2 class="font-headline-lg text-headline-lg text-on-surface font-bold">Целевые сборы отрядов</h2>
        <p class="font-body-md text-body-md text-outline">
          Прямая адресная поддержка поисковых экспедиций на местах сражений
        </p>
      </div>
      <span class="font-label-md text-label-md text-secondary font-bold flex items-center gap-1 cursor-pointer hover:underline">
        Все 6 сборов
        <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
      </span>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <FundraisingCard
        v-for="campaign in campaigns"
        :key="campaign.squadName"
        v-bind="campaign"
        @donate="openDonation(campaign)"
      />
    </div>

    <DonationModal v-model="donationOpen" :campaign="selectedCampaign" />
  </div>
</template>
