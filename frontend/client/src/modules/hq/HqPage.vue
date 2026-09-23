<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { can, useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import StateBlock from '@/ui/StateBlock.vue'

import CampaignCard from './components/CampaignCard.vue'
import DonationSheet from './components/DonationSheet.vue'
import FieldEventCard from './components/FieldEventCard.vue'
import NeedsList from './components/NeedsList.vue'
import NewNeedSheet from './components/NewNeedSheet.vue'
import NewSquadSheet from './components/NewSquadSheet.vue'
import NewTripSheet from './components/NewTripSheet.vue'
import SeasonImpactCard from './components/SeasonImpactCard.vue'
import {
  cancelTripRegistration,
  closeNeed,
  fetchHq,
  registerForTrip,
  type Need,
  type Squad,
  type Trip,
} from './data'

/** Сколько сборов показывать до «Все сборы». */
const FUNDS_PREVIEW = 2

type Sheet =
  | { kind: 'donate'; need: Need }
  | { kind: 'squad' }
  | { kind: 'trip' }
  | { kind: 'need' }
  | { kind: 'account'; text: string }

const session = useSessionStore()
const { data, loading, error, retry } = useAsync(() => fetchHq(session.hasAccount))

const sheet = ref<Sheet | null>(null)
const notice = ref<{ tone: 'success' | 'error'; text: string } | null>(null)
const showAllFunds = ref(false)
const busyTripId = ref<string | null>(null)
/** Мои выезды — копия, которую экран меняет сразу после записи, не дожидаясь перезагрузки. */
const myTrips = ref<Set<string> | null>(null)

watch(data, (overview) => (myTrips.value = overview?.myTripIds ? new Set(overview.myTripIds) : null), { immediate: true })

const squads = computed(() => new Map((data.value?.squads ?? []).map((squad) => [squad.id, squad] as const)))
const funds = computed(() => (data.value?.needs ?? []).filter((need) => need.kind === 'funds'))
const visibleFunds = computed(() => (showAllFunds.value ? funds.value : funds.value.slice(0, FUNDS_PREVIEW)))
const otherNeeds = computed(() => (data.value?.needs ?? []).filter((need) => need.kind !== 'funds'))

/** Отряды, которыми человек управляет: свои, а у модератора — все. */
const managedSquads = computed<Squad[]>(() => {
  const user = session.user
  if (!session.hasAccount || !user) return []
  const all = data.value?.squads ?? []
  return can.moderate(user) ? all : all.filter((squad) => squad.leader_id === user.id)
})
const canCreateSquad = computed(() => session.hasAccount && can.createSquad(session.user))

function canManage(squadId: string): boolean {
  const user = session.user
  if (!session.hasAccount || !user) return false
  return can.moderate(user) || squads.value.get(squadId)?.leader_id === user.id
}

/** Перечитать данные, не пряча экран за спиннером: человек только что что-то сделал и смотрит на результат. */
async function refresh(): Promise<void> {
  try {
    data.value = await fetchHq(session.hasAccount)
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  }
}

function needAccount(text: string): boolean {
  if (session.hasAccount) return false
  sheet.value = { kind: 'account', text }
  return true
}

function openDonation(need: Need): void {
  if (needAccount('Помочь отряду можно с аккаунтом')) return
  sheet.value = { kind: 'donate', need }
}

async function register(trip: Trip): Promise<void> {
  if (needAccount('Записаться на выезд можно с аккаунтом') || busyTripId.value) return
  busyTripId.value = trip.id
  notice.value = null
  try {
    await registerForTrip(trip.id)
    myTrips.value = new Set([...(myTrips.value ?? []), trip.id])
    notice.value = { tone: 'success', text: `Вы записаны: ${trip.title}. Командир отряда увидит вас в списке.` }
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    busyTripId.value = null
  }
}

async function cancel(trip: Trip): Promise<void> {
  if (busyTripId.value) return
  busyTripId.value = trip.id
  notice.value = null
  try {
    await cancelTripRegistration(trip.id)
    const next = new Set(myTrips.value ?? [])
    next.delete(trip.id)
    myTrips.value = next
    notice.value = { tone: 'success', text: 'Запись отменена — место освободилось для другого волонтёра' }
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    busyTripId.value = null
  }
}

async function finishNeed(need: Need): Promise<void> {
  try {
    await closeNeed(need.id)
    notice.value = { tone: 'success', text: `Сбор «${need.title}» закрыт` }
    await refresh()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  }
}

async function created(text: string): Promise<void> {
  sheet.value = null
  notice.value = { tone: 'success', text }
  await refresh()
}

/** Записан ли человек: `null` — неизвестно (демо), тогда кнопка «Записаться» остаётся. */
function isRegistered(tripId: string): boolean | null {
  return myTrips.value ? myTrips.value.has(tripId) : null
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-lg px-margin pb-6">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <DemoDataBadge v-if="data.source === 'demo'" />

      <SeasonImpactCard :stats="data.season" />

      <!-- Командир отряда: набор волонтёров и потребности. Поисковик без отряда: завести свой. -->
      <section
        v-if="managedSquads.length || canCreateSquad"
        class="flex flex-col gap-space-sm rounded-lg bg-secondary p-space-md text-on-secondary shadow-md"
      >
        <div class="flex items-center gap-space-sm">
          <MsIcon name="shield_person" :size="24" />
          <div class="min-w-0">
            <span class="block font-label-sm text-label-sm uppercase tracking-wider opacity-80">Штаб отряда</span>
            <span class="block truncate font-label-lg text-label-lg">
              {{ managedSquads.length ? managedSquads.map((squad) => squad.name).join(', ') : 'У вас пока нет отряда' }}
            </span>
          </div>
        </div>
        <div v-if="managedSquads.length" class="grid grid-cols-2 gap-space-sm">
          <button
            type="button"
            class="flex items-center justify-center gap-1.5 rounded-full bg-on-secondary px-3 py-2.5 font-label-md text-label-md text-secondary active:scale-95"
            @click="sheet = { kind: 'trip' }"
          >
            <MsIcon name="campaign" :size="18" />
            Набрать людей
          </button>
          <button
            type="button"
            class="flex items-center justify-center gap-1.5 rounded-full bg-on-secondary/15 px-3 py-2.5 font-label-md text-label-md text-on-secondary active:scale-95"
            @click="sheet = { kind: 'need' }"
          >
            <MsIcon name="add_circle" :size="18" />
            Что нужно
          </button>
        </div>
        <button
          v-else
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full bg-on-secondary px-3 py-2.5 font-label-md text-label-md text-secondary active:scale-95"
          @click="sheet = { kind: 'squad' }"
        >
          <MsIcon name="flag" :size="18" />
          Создать отряд
        </button>
      </section>

      <InlineNotice v-if="notice" :tone="notice.tone">{{ notice.text }}</InlineNotice>

      <section class="flex flex-col gap-space-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MsIcon name="handshake" :size="22" class="text-primary" />
            <h2 class="font-headline-md text-headline-md text-on-surface">Целевые сборы отрядов</h2>
          </div>
          <button
            v-if="funds.length > FUNDS_PREVIEW"
            type="button"
            class="font-label-md text-label-md text-primary transition-opacity hover:opacity-80"
            @click="showAllFunds = !showAllFunds"
          >
            {{ showAllFunds ? 'Свернуть' : `Все сборы (${funds.length})` }}
          </button>
        </div>
        <CampaignCard
          v-for="need in visibleFunds"
          :key="need.id"
          :need="need"
          :squad="squads.get(need.squad_id)"
          :can-manage="canManage(need.squad_id)"
          @donate="openDonation(need)"
          @close="finishNeed(need)"
        />
        <StateBlock v-if="!funds.length" :loading="false" :error="null" empty empty-icon="savings" empty-text="Открытых сборов сейчас нет" />
      </section>

      <section v-if="otherNeeds.length" class="flex flex-col gap-space-sm">
        <div class="flex items-center gap-2">
          <MsIcon name="emergency_home" :size="22" class="text-tertiary" />
          <h2 class="font-headline-md text-headline-md text-on-surface">Нужна помощь отрядам</h2>
        </div>
        <NeedsList :needs="otherNeeds" :squads="squads" />
      </section>

      <section class="flex flex-col gap-space-sm">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <MsIcon name="backpack" :size="22" class="text-secondary" />
            <h2 class="font-headline-md text-headline-md text-on-surface">Выходные с поисковиком</h2>
          </div>
          <span class="rounded-full bg-field px-2.5 py-1 font-label-sm text-label-sm text-on-secondary">Полевая школа</span>
        </div>
        <FieldEventCard
          v-for="trip in data.trips"
          :key="trip.id"
          :trip="trip"
          :squad="squads.get(trip.squad_id)"
          :registered="isRegistered(trip.id)"
          :busy="busyTripId === trip.id"
          :can-manage="canManage(trip.squad_id)"
          @register="register(trip)"
          @cancel="cancel(trip)"
        />
        <StateBlock
          v-if="!data.trips.length"
          :loading="false"
          :error="null"
          empty
          empty-icon="event_busy"
          empty-text="Ближайших выездов пока нет — загляните позже"
        />
      </section>
    </template>

    <DonationSheet
      v-if="sheet?.kind === 'donate'"
      :need="sheet.need"
      :squad="squads.get(sheet.need.squad_id)"
      @donated="refresh"
      @close="sheet = null"
    />
    <NewSquadSheet v-else-if="sheet?.kind === 'squad'" @created="(squad) => created(`${squad.name}: отряд создан, вы его командир`)" @close="sheet = null" />
    <NewTripSheet
      v-else-if="sheet?.kind === 'trip'"
      :squads="managedSquads"
      @created="(trip) => created(`Набор объявлен: ${trip.title}`)"
      @close="sheet = null"
    />
    <NewNeedSheet
      v-else-if="sheet?.kind === 'need'"
      :squads="managedSquads"
      @created="(need) => created(`Опубликовано: ${need.title}`)"
      @close="sheet = null"
    />
    <SheetDialog v-else-if="sheet?.kind === 'account'" title="Нужен аккаунт" @close="sheet = null">
      <AccountRequired :text="sheet.text" />
    </SheetDialog>
  </div>
</template>
