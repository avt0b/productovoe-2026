<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText, plural } from '@/core/format'
import { can, useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SegmentTabs from '@/ui/SegmentTabs.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import StateBlock from '@/ui/StateBlock.vue'

import CampaignCard from './components/CampaignCard.vue'
import DonationSheet from './components/DonationSheet.vue'
import FieldEventCard from './components/FieldEventCard.vue'
import NeedsList from './components/NeedsList.vue'
import NeedsMap from './components/NeedsMap.vue'
import NewNeedSheet from './components/NewNeedSheet.vue'
import NewSquadSheet from './components/NewSquadSheet.vue'
import NewTripSheet from './components/NewTripSheet.vue'
import SeasonImpactCard from './components/SeasonImpactCard.vue'
import TripCalendar from './components/TripCalendar.vue'
import {
  CAMPAIGN_KINDS,
  campaignOf,
  cancelTripRegistration,
  closeNeed,
  fetchHq,
  registerForTrip,
  type CampaignKind,
  type Need,
  type Squad,
  type Trip,
  type TripFilter,
} from './data'

/** Сколько сборов показывать до «Ещё». */
const FUNDS_PREVIEW = 2

type Tab = 'funds' | 'trips' | 'squads'
const TABS: readonly Tab[] = ['funds', 'trips', 'squads']

type Sheet =
  | { kind: 'donate'; need: Need }
  | { kind: 'squad'; squad?: Squad }
  | { kind: 'trip' }
  | { kind: 'need' }
  | { kind: 'account'; text: string }

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const { data, loading, error, retry } = useAsync(() => fetchHq(session.hasAccount))

/**
 * Режим живёт в адресе: «Я готов помочь в подъёме» из «Последнего боя» ведёт
 * сразу к выездам, а «Назад» возвращает туда, где человек был.
 */
const tab = computed<Tab>({
  get: () => (TABS.includes(route.query.tab as Tab) ? (route.query.tab as Tab) : 'funds'),
  set: (value) => void switchTab(value),
})

async function switchTab(value: Tab): Promise<void> {
  await router.replace({ query: { ...route.query, tab: value === 'funds' ? undefined : value } })
}

const sheet = ref<Sheet | null>(null)
const notice = ref<{ tone: 'success' | 'error'; text: string } | null>(null)
const showAllFunds = ref(false)
const campaignFilter = ref<CampaignKind | 'all'>('all')
const tripFilter = ref<TripFilter>('all')
const busyTripId = ref<string | null>(null)
const closingNeedId = ref<string | null>(null)
const focusedTripId = ref<string | null>(null)
/** Мои выезды — копия, которую экран меняет сразу после записи, не дожидаясь перезагрузки. */
const myTrips = ref<Set<string> | null>(null)

watch(data, (overview) => (myTrips.value = overview?.myTripIds ? new Set(overview.myTripIds) : null), { immediate: true })

const squads = computed(() => new Map((data.value?.squads ?? []).map((squad) => [squad.id, squad] as const)))
const funds = computed(() => (data.value?.needs ?? []).filter((need) => need.kind === 'funds'))
const otherNeeds = computed(() => (data.value?.needs ?? []).filter((need) => need.kind !== 'funds'))

/** Фильтр по виду сбора — только когда есть из чего выбирать. */
const campaignOptions = computed(() => {
  const present = new Set(funds.value.map((need) => campaignOf(need).kind))
  const kinds = (Object.keys(CAMPAIGN_KINDS) as CampaignKind[]).filter((kind) => present.has(kind))
  if (kinds.length < 2) return []
  return [
    { value: 'all' as const, title: 'Все', icon: 'savings' },
    ...kinds.map((kind) => ({ value: kind, title: CAMPAIGN_KINDS[kind].title, icon: CAMPAIGN_KINDS[kind].icon })),
  ]
})
const filteredFunds = computed(() =>
  campaignFilter.value === 'all' ? funds.value : funds.value.filter((need) => campaignOf(need).kind === campaignFilter.value),
)
const previewFunds = computed(() => filteredFunds.value.slice(0, FUNDS_PREVIEW))
const restFunds = computed(() => filteredFunds.value.slice(FUNDS_PREVIEW))

const trips = computed(() => [...(data.value?.trips ?? [])].sort((a, b) => a.starts_on.localeCompare(b.starts_on)))
const visibleTrips = computed(() => {
  const filter = tripFilter.value
  if (filter === 'all') return trips.value
  if (filter === 'mine') return trips.value.filter((trip) => myTrips.value?.has(trip.id))
  return trips.value.filter((trip) => trip.starts_on === filter)
})
/** Ближайший выезд каждого отряда — куда вести с «нужны люди» и с карты. */
const nextTrips = computed(() => {
  const next = new Map<string, Trip>()
  for (const trip of trips.value) if (!next.has(trip.squad_id)) next.set(trip.squad_id, trip)
  return next
})

const tabs = computed(() => [
  { value: 'funds' as const, title: 'Сборы', icon: 'savings', count: funds.value.length },
  { value: 'trips' as const, title: 'Выезды', icon: 'event', count: trips.value.length },
  { value: 'squads' as const, title: 'Отряды', icon: 'map' },
])

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

/** Привести к выезду с другого блока: режим «Выезды», фильтр снят, карточка подсвечена. */
async function showTrip(tripId: string): Promise<void> {
  tripFilter.value = 'all'
  focusedTripId.value = tripId
  // Режим меняется через адрес — ждём, пока роутер его применит и карточка появится.
  await switchTab('trips')
  await nextTick()
  document.getElementById(`hq-trip-${tripId}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  setTimeout(() => {
    if (focusedTripId.value === tripId) focusedTripId.value = null
  }, 2400)
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
    if (tripFilter.value === 'mine' && next.size === 0) tripFilter.value = 'all'
    notice.value = { tone: 'success', text: 'Запись отменена — место освободилось для другого волонтёра' }
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    busyTripId.value = null
  }
}

async function finishNeed(need: Need): Promise<void> {
  if (closingNeedId.value) return
  closingNeedId.value = need.id
  try {
    await closeNeed(need.id)
    notice.value = { tone: 'success', text: `Сбор «${need.title}» закрыт` }
    await refresh()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    closingNeedId.value = null
  }
}

async function created(text: string, nextTab?: Tab): Promise<void> {
  sheet.value = null
  notice.value = { tone: 'success', text }
  if (nextTab) await switchTab(nextTab)
  await refresh()
}

/** Записан ли человек: `null` — неизвестно (демо), тогда кнопка «Записаться» остаётся. */
function isRegistered(tripId: string): boolean | null {
  return myTrips.value ? myTrips.value.has(tripId) : null
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin short:gap-space-sm">
    <header class="flex flex-col gap-space-xs">
      <p class="font-archival text-archival uppercase text-on-surface-variant">Поисковый штаб · Орловская область</p>
      <h1
        class="ribbon-shimmer font-headline-lg text-headline-lg text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)] short:text-headline-lg-mobile"
      >
        Штаб
      </h1>
      <p class="font-body-sm text-body-sm text-on-surface-variant">Отрядам нужны руки, деньги и снаряжение — выберите, чем помочь</p>
    </header>

    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <DemoDataBadge v-if="data.source === 'demo'" />

      <SeasonImpactCard :stats="data.season" />

      <!-- Командир отряда: набор волонтёров и потребности. Поисковик без отряда: завести свой. -->
      <section
        v-if="managedSquads.length || canCreateSquad"
        class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document"
      >
        <div class="flex items-center gap-space-sm">
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
            aria-hidden="true"
          >
            <MsIcon name="shield_person" :size="22" />
          </span>
          <div class="min-w-0">
            <p class="font-archival text-archival uppercase text-on-surface-variant">Штаб отряда</p>
            <p class="truncate font-headline-sm text-headline-sm text-on-surface">
              {{ managedSquads.length ? managedSquads.map((squad) => squad.name).join(', ') : 'У вас пока нет отряда' }}
            </p>
          </div>
        </div>
        <template v-if="managedSquads.length">
          <!-- Командир правит сведения отряда: их видят волонтёры на карте потребностей. -->
          <div class="flex flex-wrap gap-space-xs">
            <button
              v-for="squad in managedSquads"
              :key="squad.id"
              type="button"
              class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
              @click="sheet = { kind: 'squad', squad }"
            >
              <MsIcon name="edit" :size="18" />
              <span class="max-w-40 truncate">{{ squad.name }}</span>
            </button>
          </div>
          <button
            type="button"
            class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
            @click="sheet = { kind: 'trip' }"
          >
            <MsIcon name="campaign" :size="18" />
            <span>Набрать волонтёров</span>
          </button>
          <button
            type="button"
            class="flex items-center justify-center gap-space-xs self-center rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="sheet = { kind: 'need' }"
          >
            <MsIcon name="add_circle" :size="18" />
            Что нужно отряду
          </button>
        </template>
        <template v-else>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Заведите отряд — и сможете объявлять выезды, собирать на экспедиции и искать людей.
          </p>
          <button
            type="button"
            class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
            @click="sheet = { kind: 'squad' }"
          >
            <MsIcon name="flag" :size="18" />
            <span>Создать отряд</span>
          </button>
        </template>
      </section>

      <InlineNotice v-if="notice" :tone="notice.tone">{{ notice.text }}</InlineNotice>

      <SegmentTabs v-model="tab" :tabs="tabs" label="Разделы штаба" id-prefix="hq" />

      <!-- Сборы: «Поднять бойца», «Экипировать отряд» и всё, что нужно без денег. -->
      <section v-if="tab === 'funds'" id="hq-funds" role="tabpanel" aria-labelledby="hq-tab-funds" class="flex flex-col gap-space-md">
        <div
          v-if="campaignOptions.length"
          class="no-scrollbar -mx-margin -my-1 flex gap-space-xs overflow-x-auto px-margin py-1"
          role="radiogroup"
          aria-label="Вид сбора"
        >
          <button
            v-for="option in campaignOptions"
            :key="option.value"
            type="button"
            role="radio"
            :aria-checked="campaignFilter === option.value"
            class="flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full px-space-sm py-1.5 font-label-md text-label-md transition-colors duration-200 active:scale-95"
            :class="
              campaignFilter === option.value
                ? 'bg-secondary text-on-secondary'
                : 'bg-surface-container-lowest text-on-surface-variant shadow-document'
            "
            @click="campaignFilter = option.value"
          >
            <MsIcon :name="option.icon" :size="15" />
            {{ option.title }}
          </button>
        </div>

        <div class="flex flex-col gap-space-sm">
          <CampaignCard
            v-for="need in previewFunds"
            :key="need.id"
            :need="need"
            :squad="squads.get(need.squad_id)"
            :can-manage="canManage(need.squad_id)"
            :closing="closingNeedId === need.id"
            @donate="openDonation(need)"
            @close="finishNeed(need)"
          />
          <div
            v-if="restFunds.length"
            class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
            :class="showAllFunds ? 'grid-rows-[1fr] opacity-100' : '-mt-space-sm grid-rows-[0fr] opacity-0'"
            :inert="!showAllFunds"
          >
            <div class="flex flex-col gap-space-sm overflow-hidden">
              <CampaignCard
                v-for="need in restFunds"
                :key="need.id"
                :need="need"
                :squad="squads.get(need.squad_id)"
                :can-manage="canManage(need.squad_id)"
                :closing="closingNeedId === need.id"
                @donate="openDonation(need)"
                @close="finishNeed(need)"
              />
            </div>
          </div>
          <button
            v-if="restFunds.length"
            type="button"
            class="flex items-center justify-center gap-space-xs self-center rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            :aria-expanded="showAllFunds"
            @click="showAllFunds = !showAllFunds"
          >
            {{ showAllFunds ? 'Свернуть' : `Ещё ${restFunds.length} ${plural(restFunds.length, ['сбор', 'сбора', 'сборов'])}` }}
            <MsIcon name="expand_more" :size="18" class="transition-transform duration-300" :class="{ 'rotate-180': showAllFunds }" />
          </button>
          <StateBlock
            v-if="!filteredFunds.length"
            :loading="false"
            :error="null"
            empty
            empty-icon="savings"
            empty-text="Открытых сборов сейчас нет"
          />
        </div>

        <div v-if="otherNeeds.length" class="flex flex-col gap-space-sm">
          <div>
            <p class="font-archival text-archival uppercase text-on-surface-variant">Без денег</p>
            <h2 class="font-headline-md text-headline-md text-on-surface">Нужна помощь руками</h2>
          </div>
          <NeedsList :needs="otherNeeds" :squads="squads" :next-trips="nextTrips" @trip="showTrip" />
        </div>
      </section>

      <!-- «Выходные с поисковиком»: календарь выездов, запись и чек-лист подготовки. -->
      <section v-else-if="tab === 'trips'" id="hq-trips" role="tabpanel" aria-labelledby="hq-tab-trips" class="flex flex-col gap-space-sm">
        <div>
          <p class="font-archival text-archival uppercase text-on-surface-variant">Полевая школа</p>
          <h2 class="font-headline-md text-headline-md text-on-surface">Выходные с поисковиком</h2>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Опыт не нужен — командир всему научит на месте. Чек-лист подскажет, что взять.
          </p>
        </div>

        <TripCalendar v-if="trips.length" v-model="tripFilter" :trips="trips" :mine="myTrips" />

        <FieldEventCard
          v-for="trip in visibleTrips"
          :id="`hq-trip-${trip.id}`"
          :key="trip.id"
          :trip="trip"
          :squad="squads.get(trip.squad_id)"
          :registered="isRegistered(trip.id)"
          :busy="busyTripId === trip.id"
          :can-manage="canManage(trip.squad_id)"
          :focused="focusedTripId === trip.id"
          @register="register(trip)"
          @cancel="cancel(trip)"
        />
        <StateBlock
          v-if="!visibleTrips.length"
          :loading="false"
          :error="null"
          empty
          empty-icon="event_busy"
          empty-text="Ближайших выездов пока нет — загляните позже"
        />
      </section>

      <!-- Карта потребностей: где какой отряд и что ему нужно. -->
      <section v-else id="hq-squads" role="tabpanel" aria-labelledby="hq-tab-squads" class="flex flex-col gap-space-sm">
        <div>
          <p class="font-archival text-archival uppercase text-on-surface-variant">Карта потребностей</p>
          <h2 class="font-headline-md text-headline-md text-on-surface">Кому что нужно</h2>
        </div>
        <NeedsMap :squads="data.squads" :needs="data.needs" :next-trips="nextTrips" @donate="openDonation" @trip="showTrip" />
      </section>
    </template>

    <DonationSheet
      v-if="sheet?.kind === 'donate'"
      :need="sheet.need"
      :squad="squads.get(sheet.need.squad_id)"
      @donated="refresh"
      @close="sheet = null"
    />
    <NewSquadSheet
      v-else-if="sheet?.kind === 'squad'"
      :squad="sheet.squad ?? null"
      @created="(squad) => created(sheet?.kind === 'squad' && sheet.squad ? `${squad.name}: сведения обновлены` : `${squad.name}: отряд создан, вы его командир`)"
      @removed="(squad) => created(`${squad.name}: отряд распущен`)"
      @close="sheet = null"
    />
    <NewTripSheet
      v-else-if="sheet?.kind === 'trip'"
      :squads="managedSquads"
      @created="(trip) => created(`Набор объявлен: ${trip.title}`, 'trips')"
      @close="sheet = null"
    />
    <NewNeedSheet
      v-else-if="sheet?.kind === 'need'"
      :squads="managedSquads"
      @created="(need) => created(`Опубликовано: ${need.title}`, 'funds')"
      @close="sheet = null"
    />
    <SheetDialog v-else-if="sheet?.kind === 'account'" title="Нужен аккаунт" @close="sheet = null">
      <AccountRequired :text="sheet.text" />
    </SheetDialog>
  </div>
</template>
