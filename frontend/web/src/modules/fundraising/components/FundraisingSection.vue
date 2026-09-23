<script setup>
import { computed, onMounted, ref } from 'vue'
import FundraisingCard from './FundraisingCard.vue'
import DonationModal from './DonationModal.vue'
import * as fundraisingApi from '../api.js'

const needs = ref([])
const squadsById = ref({})
const loadStatus = ref('idle') // idle | loading | loaded | error

async function load() {
  loadStatus.value = 'loading'
  try {
    const [needsList, squadsList] = await Promise.all([
      fundraisingApi.listNeeds({ kind: 'funds' }),
      fundraisingApi.listSquads(),
    ])
    needs.value = needsList
    squadsById.value = Object.fromEntries(squadsList.map((s) => [s.id, s]))
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

onMounted(load)

const campaigns = computed(() =>
  [...needs.value]
    .sort((a, b) => (a.status === b.status ? 0 : a.status === 'open' ? -1 : 1))
    .map((need) => {
    const squad = squadsById.value[need.squad_id]
    const percent = need.target_amount ? Math.min(100, Math.round((need.collected_amount / need.target_amount) * 100)) : 0
    return {
      id: need.id,
      squadName: squad?.name || 'Отряд неизвестен',
      location: squad?.region || '',
      tag: 'Целевой сбор',
      tagClass: 'bg-surface-container-high text-on-surface-variant',
      title: need.title,
      text: need.description,
      raised: `${need.collected_amount.toLocaleString('ru-RU')} ₽`,
      goal: need.target_amount ? `из ${need.target_amount.toLocaleString('ru-RU')} ₽` : 'без цели',
      percent,
      statusLabel: need.status === 'open' ? 'Сбор открыт' : 'Сбор закрыт',
      barClass: 'bg-primary',
      raisedTextClass: 'text-primary',
      ctaLabel: need.status === 'open' ? 'Помочь отряду' : 'Сбор завершён',
      ctaClass:
        need.status === 'open'
          ? 'bg-primary hover:bg-primary/90 text-on-primary shadow-md'
          : 'bg-surface-container text-on-surface-variant cursor-not-allowed',
      ctaIcon: 'volunteer_activism',
    }
  }),
)

const donationOpen = ref(false)
const selectedCampaign = ref(null)

function openDonation(campaign) {
  if (campaign.ctaLabel === 'Сбор завершён') return
  selectedCampaign.value = campaign
  donationOpen.value = true
}

function onDonated() {
  // Бэкенд сам закрывает сбор, когда collected_amount достигает target_amount
  // (NeedService._credit) — локально просто прибавлять сумму недостаточно,
  // status тоже может смениться на closed. Перезагружаем список целиком,
  // чтобы карточка и кнопка сразу отражали реальное состояние с бэка.
  load()
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
      <div>
        <h2 class="font-headline-lg text-headline-lg text-on-surface font-bold">Целевые сборы отрядов</h2>
        <p class="font-body-md text-body-md text-outline">
          Прямая адресная поддержка поисковых экспедиций — данные из search_hq_service
        </p>
      </div>
    </div>

    <p
      v-if="loadStatus === 'loaded' && !campaigns.length"
      class="bg-surface-container-lowest rounded-lg p-6 text-on-surface-variant font-body-md text-body-md"
    >
      В search_hq_service пока нет денежных сборов.
    </p>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <FundraisingCard
        v-for="campaign in campaigns"
        :key="campaign.id"
        v-bind="campaign"
        @donate="openDonation(campaign)"
      />
    </div>

    <DonationModal v-model="donationOpen" :campaign="selectedCampaign" @donated="onDonated" />
  </div>
</template>
