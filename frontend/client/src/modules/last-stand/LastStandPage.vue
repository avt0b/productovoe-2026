<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText, plural } from '@/core/format'
import { distanceKm, formatDistance, geolocationProblem, useGeolocation, type GeoMarker } from '@/core/geo'
import { can, useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import DemoDataBadge from '@/ui/DemoDataBadge.vue'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import StateBlock from '@/ui/StateBlock.vue'

import AddPointSheet from './components/AddPointSheet.vue'
import EvidenceSheet from './components/EvidenceSheet.vue'
import RecordCard from './components/RecordCard.vue'
import RegistryList from './components/RegistryList.vue'
import StatusFilters from './components/StatusFilters.vue'
import SubscriptionSheet from './components/SubscriptionSheet.vue'
import {
  STATUS_LABELS,
  STATUS_STYLE,
  fetchLastStand,
  fetchSubscription,
  setPointStatus,
  type FindRecord,
  type FindStatus,
  type MapCircle,
  type SearchSubscription,
} from './data'

type Sheet =
  | { kind: 'add' }
  | { kind: 'evidence'; record: FindRecord }
  | { kind: 'subscribe' }
  | { kind: 'account'; text: string }

const router = useRouter()
const session = useSessionStore()
const { data, loading, error, retry } = useAsync(fetchLastStand)

const sheet = ref<Sheet | null>(null)
const notice = ref<{ tone: 'success' | 'error'; text: string } | null>(null)
const statusBusy = ref(false)

/** Кто отмечает места: поисковик, краевед, наставник, модератор. Семье кнопку не показываем. */
const canAdd = computed(() => session.hasAccount && can.addLastStand(session.user))
const canModerate = computed(() => session.hasAccount && can.moderate(session.user))
/** «Готов помочь» ведёт к выездам отрядов — если окно «Штаб» подключено. */
const canVolunteer = computed(() => router.hasRoute('hq'))

/** Перечитать места, не пряча карту за спиннером. */
async function refresh(): Promise<void> {
  try {
    data.value = await fetchLastStand()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  }
}

async function pointAdded(): Promise<void> {
  sheet.value = null
  notice.value = { tone: 'success', text: 'Место отмечено со статусом «Обнаружено» — модератор проверит его по архиву' }
  await refresh()
}

function openEvidence(record: FindRecord): void {
  sheet.value = session.hasAccount
    ? { kind: 'evidence', record }
    : { kind: 'account', text: 'Дополнить сведения о месте можно с аккаунтом' }
}

async function changeStatus(record: FindRecord, status: FindStatus): Promise<void> {
  statusBusy.value = true
  try {
    await setPointStatus(record.id, status)
    notice.value = { tone: 'success', text: `${record.title}: ${STATUS_LABELS[status].toLowerCase()}` }
    await refresh()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    statusBusy.value = false
  }
}

// --- подписка на район ---

const subscription = ref<SearchSubscription | null>(null)

// Подписка — удобство, а не условие экрана: не загрузилась — карта и реестр
// работают как работали, просто без круга района.
onMounted(async () => {
  if (!session.hasAccount) return
  try {
    subscription.value = await fetchSubscription()
  } catch {
    subscription.value = null
  }
})

function openSubscription(): void {
  sheet.value = session.hasAccount
    ? { kind: 'subscribe' }
    : { kind: 'account', text: 'Сообщать о находках рядом можем только тем, у кого есть аккаунт' }
}

function subscriptionSaved(saved: SearchSubscription): void {
  subscription.value = saved
  sheet.value = null
  notice.value = saved.subscribed
    ? { tone: 'success', text: `Сообщим о новых местах гибели в ${saved.radiusKm} км от выбранной точки` }
    : { tone: 'success', text: 'Больше не будем сообщать о находках рядом' }
}

const subscriptionLabel = computed(() => {
  const current = subscription.value
  if (current?.subscribed && current.home) return `Сообщаем о находках в ${current.radiusKm} км — изменить`
  return 'Сообщать о находках рядом'
})

/** Район подписки на карте: видно, какие места попадают в «рядом». */
const circles = computed<MapCircle[]>(() => {
  const current = subscription.value
  if (!current?.subscribed || !current.home) return []
  return [{ id: 'subscription', ...current.home, radiusMeters: current.radiusKm * 1000, tone: 'secondary' }]
})

// --- карта и выбор места ---

const { position: userPosition, status: geoStatus, start: startLocating } = useGeolocation()

/** Какие стадии находок показывать. По умолчанию — все. */
const visibleStatuses = ref<Set<FindStatus>>(new Set(['found', 'confirmed', 'raised']))
const selectedId = ref<string | null>(null)

const records = computed(() => data.value?.records ?? [])
const visibleRecords = computed(() => records.value.filter((record) => visibleStatuses.value.has(record.status)))

const counts = computed<Record<FindStatus, number>>(() => {
  const result: Record<FindStatus, number> = { found: 0, confirmed: 0, raised: 0 }
  for (const record of records.value) result[record.status] += 1
  return result
})

const markers = computed<GeoMarker[]>(() =>
  visibleRecords.value.map((record) => ({
    id: record.id,
    lat: record.lat,
    lon: record.lon,
    label: record.title,
    icon: STATUS_STYLE[record.status].icon,
    tone: STATUS_STYLE[record.status].tone,
  })),
)

// Сначала открыта точка, которой нужна помощь. Если выбранную метку скрыли
// фильтром — переключаемся на первую видимую, а не держим пустую карточку.
watch(
  visibleRecords,
  (list) => {
    if (list.some((record) => record.id === selectedId.value)) return
    selectedId.value = (list.find((record) => record.status === 'found') ?? list[0])?.id ?? null
  },
  { immediate: true },
)

const selectedRecord = computed(() => visibleRecords.value.find((record) => record.id === selectedId.value) ?? null)

const recordCard = ref<HTMLElement | null>(null)

/** Выбор из реестра: карточка места — над списком, её надо показать. */
async function selectFromRegistry(id: string): Promise<void> {
  selectedId.value = id
  await nextTick()
  recordCard.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// --- «внимание поисковика» ---

const needHelp = computed(() => records.value.filter((record) => record.status === 'found'))

/** До ближайшего такого места — если известно, где человек. Это та самая строка «в 5 км от вас» из кейса. */
const nearestNeedKm = computed(() => {
  const user = userPosition.value
  if (!user || needHelp.value.length === 0) return null
  return Math.min(...needHelp.value.map((record) => distanceKm(user, record)))
})

const alertDistance = computed(() =>
  nearestNeedKm.value === null ? 'Орловская обл.' : `ближайшее в ${formatDistance(nearestNeedKm.value)}`,
)

const alertTitle = computed(() => {
  const count = needHelp.value.length
  if (count === 0) return 'Все места проверены'
  return `${count} ${plural(count, ['место ждёт', 'места ждут', 'мест ждут'])} проверки`
})

const alertText = computed(() =>
  needHelp.value.length === 0
    ? 'Новые точки появятся здесь, как только их отметят поисковые отряды.'
    : 'Помогите архивистам и поисковикам: сверьте место с Книгой Памяти или расскажите, что знаете.',
)

const geoProblem = computed(() => geolocationProblem(geoStatus.value))
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin short:gap-space-sm">
    <header class="flex flex-col gap-space-xs">
      <p class="font-archival text-archival uppercase text-on-surface-variant">Поисковый реестр · Орловская область</p>
      <h1
        class="ribbon-shimmer font-headline-lg text-headline-lg text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)] short:text-headline-lg-mobile"
      >
        Последний бой
      </h1>
      <p class="font-body-sm text-body-sm text-on-surface-variant">
        Места гибели красноармейцев — от первой находки до захоронения
      </p>
    </header>

    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="data">
      <DemoDataBadge v-if="data.source === 'demo'" />

      <section class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <div class="flex items-start gap-space-sm">
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
            aria-hidden="true"
          >
            <MsIcon name="radar" :size="22" />
          </span>
          <div class="flex min-w-0 flex-1 flex-col gap-0.5">
            <div class="flex items-center justify-between gap-space-xs">
              <p class="font-archival text-archival uppercase text-on-surface-variant">Внимание поисковика</p>
              <span class="shrink-0 font-label-sm text-label-sm text-secondary">{{ alertDistance }}</span>
            </div>
            <p class="font-headline-sm text-headline-sm text-on-surface">{{ alertTitle }}</p>
            <p class="font-body-sm text-body-sm text-on-surface-variant">{{ alertText }}</p>
          </div>
        </div>
        <button
          type="button"
          class="flex items-center justify-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="openSubscription"
        >
          <MsIcon :name="subscription?.subscribed ? 'notifications_active' : 'notifications'" :size="18" :filled="subscription?.subscribed" />
          {{ subscriptionLabel }}
        </button>
      </section>

      <button
        v-if="canAdd"
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="sheet = { kind: 'add' }"
      >
        <MsIcon name="add_location_alt" :size="18" />
        <span>Отметить место гибели</span>
      </button>

      <InlineNotice v-if="notice" :tone="notice.tone">{{ notice.text }}</InlineNotice>

      <StatusFilters v-model="visibleStatuses" :counts="counts" />

      <GeoMap
        v-model:selected="selectedId"
        :markers="markers"
        :circles="circles"
        :user="userPosition"
        :locating="geoStatus === 'locating'"
        label="Орловская область"
        class="h-80 w-full rounded-2xl shadow-document short:h-64"
        @locate="startLocating"
      />

      <InlineNotice v-if="geoProblem" tone="info" icon="location_off">{{ geoProblem }}</InlineNotice>

      <div ref="recordCard" class="scroll-mt-space-md">
        <RecordCard
          v-if="selectedRecord"
          :key="selectedRecord.id"
          :record="selectedRecord"
          :can-volunteer="canVolunteer"
          :volunteer-is-primary="!canAdd"
          :can-moderate="canModerate"
          :busy="statusBusy"
          @volunteer="router.push({ name: 'hq', query: { tab: 'trips' } })"
          @add-data="openEvidence(selectedRecord)"
          @set-status="(status) => selectedRecord && changeStatus(selectedRecord, status)"
        />
        <StateBlock
          v-else
          :loading="false"
          :error="null"
          empty
          empty-icon="filter_alt_off"
          empty-text="Под выбранные фильтры мест нет — включите стадию выше"
        />
      </div>

      <RegistryList :records="visibleRecords" :selected-id="selectedId" :from="userPosition" @select="selectFromRegistry" />
    </template>

    <AddPointSheet v-if="sheet?.kind === 'add'" @created="pointAdded" @close="sheet = null" />
    <EvidenceSheet v-else-if="sheet?.kind === 'evidence'" :record="sheet.record" @close="sheet = null" />
    <SubscriptionSheet v-else-if="sheet?.kind === 'subscribe'" @saved="subscriptionSaved" @close="sheet = null" />
    <SheetDialog v-else-if="sheet?.kind === 'account'" title="Нужен аккаунт" @close="sheet = null">
      <AccountRequired :text="sheet.text" />
    </SheetDialog>
  </div>
</template>
