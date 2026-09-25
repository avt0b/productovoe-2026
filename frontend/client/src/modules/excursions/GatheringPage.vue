<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText, plural } from '@/core/format'
import { geolocationProblem, useGeolocation } from '@/core/geo'
import { useSessionStore } from '@/core/session'
import { BumpPad, TogetherOverlay, useBump } from '@/features/bump'
import AccountRequired from '@/ui/AccountRequired.vue'
import ConfirmAction from '@/ui/ConfirmAction.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import DestinationPicker from './components/DestinationPicker.vue'
import {
  fetchExcursion,
  fetchGathering,
  finishGathering,
  leadWalk,
  nextStop,
  startGathering,
  stopTargets,
  toPosition,
  type Gathering,
  type Position,
  type WalkTarget,
} from './data'
import { formatTime, minutesLeft, participantLabel } from './format'

const props = defineProps<{ excursionId: string }>()

/** Как часто обновлять счётчик группы, мс. */
const POLL_MS = 4000
/** Сколько ждать первого фикса GPS перед открытием сбора, мс. */
const FIRST_FIX_TIMEOUT_MS = 20_000
/** Через сколько считать, что датчик движения молчит, мс. */
const SENSOR_SILENCE_MS = 3000

type Notice = { tone: 'info' | 'error' | 'success'; text: string }

const session = useSessionStore()
const router = useRouter()
const { data: excursion, loading, error, retry } = useAsync(() => fetchExcursion(props.excursionId, true))
const { position, status: geoStatus, start: startLocating } = useGeolocation()

const gathering = shallowRef<Gathering | null>(null)
/** `setup` — ждём нажатия: разрешения на GPS и датчик спрашиваются только из нажатия. */
const phase = ref<'setup' | 'active'>('setup')
const opening = ref(false)
const closing = ref(false)
const sensorSilent = ref(false)
const notice = ref<Notice | null>(null)
const now = ref(Date.now())

const isGuide = computed(() => excursion.value?.viewer?.is_guide === true)
const isRegistered = computed(() => excursion.value?.viewer?.registered === true)
const isOpen = computed(() => gathering.value?.is_open ?? excursion.value?.status === 'gathering')
const checkedInAt = computed(() => gathering.value?.my_checked_in_at ?? excursion.value?.viewer?.checked_in_at ?? null)
const minutes = computed(() => minutesLeft(gathering.value?.ends_at ?? excursion.value?.gathering_ends_at ?? null, now.value))
const geoProblem = computed(() => geolocationProblem(geoStatus.value))

const partnerWord = computed(() => (isGuide.value ? 'с участником' : 'с краеведом'))

/** Сам бамп — модуль `features/bump`: датчик, встряска на сервер, «Вы вместе!». */
const bump = useBump({
  excursionId: () => props.excursionId,
  isGuide: () => isGuide.value,
  isOpen: () => isOpen.value,
  position,
  afterBump: () => refreshGathering(),
})
const { sensor, sending, together } = bump
const intensity = sensor.intensity

/** Сообщения экрана: свои (открытие сбора) и бампа — показываем последнее. */
watch(bump.notice, (value) => (notice.value = value))

const padHeadline = computed(() => {
  if (!isOpen.value) return 'Ждём открытия сбора'
  if (!isGuide.value && checkedInAt.value) return 'Вы уже в группе'
  return `Встряхните телефон одновременно ${partnerWord.value}`
})

const sensorProblem = computed(() => {
  if (sensor.status.value === 'denied') return 'Доступ к датчику движения запрещён — нажимайте «Встряхнуть» одновременно.'
  if (sensor.status.value === 'unsupported' || sensorSilent.value) return 'Датчик движения не отвечает — нажимайте «Встряхнуть» одновременно.'
  return null
})

let clockTimer: ReturnType<typeof setInterval> | undefined
let pollTimer: ReturnType<typeof setInterval> | undefined
let silenceTimer: ReturnType<typeof setTimeout> | undefined

onMounted(() => {
  clockTimer = setInterval(() => (now.value = Date.now()), 1000)
  pollTimer = setInterval(() => void refreshGathering(), POLL_MS)
  void refreshGathering()
})

onBeforeUnmount(() => {
  clearInterval(clockTimer)
  clearInterval(pollTimer)
  clearTimeout(silenceTimer)
})

async function refreshGathering(): Promise<void> {
  if (!session.hasAccount) return
  try {
    gathering.value = await fetchGathering(props.excursionId)
  } catch {
    // Не записан или сеть мигнула — экран покажет это по данным экскурсии, опрос продолжится.
  }
}

// Сбор закрыли (краевед или срок вышел) — датчик больше не нужен.
watch(isOpen, (open, wasOpen) => {
  if (wasOpen && !open) {
    sensor.stop()
    notice.value = { tone: 'info', text: 'Сбор группы закрыт' }
  }
})

async function getReady(): Promise<void> {
  startLocating()
  await sensor.start()
  phase.value = 'active'
  silenceTimer = setTimeout(() => (sensorSilent.value = !sensor.sensorAlive.value), SENSOR_SILENCE_MS)
  if (isGuide.value && !isOpen.value) await openGathering()
}

function waitForPosition(timeoutMs: number): Promise<Position | null> {
  if (position.value) return Promise.resolve(toPosition(position.value))
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      stopWatch()
      resolve(null)
    }, timeoutMs)
    const stopWatch = watch(position, (fix) => {
      if (!fix) return
      clearTimeout(timer)
      stopWatch()
      resolve(toPosition(fix))
    })
  })
}

async function openGathering(): Promise<void> {
  if (opening.value) return
  opening.value = true
  notice.value = { tone: 'info', text: 'Определяем, что вы у места экскурсии…' }
  try {
    const where = await waitForPosition(FIRST_FIX_TIMEOUT_MS)
    if (!where) {
      notice.value = { tone: 'error', text: geoProblem.value ?? 'Не удалось определить местоположение — выйдите на открытое место' }
      return
    }
    gathering.value = await startGathering(props.excursionId, where)
    notice.value = { tone: 'success', text: 'Сбор открыт — встряхивайте телефон вместе с каждым участником' }
    await retry()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    opening.value = false
  }
}


async function finish(): Promise<void> {
  if (closing.value) return
  closing.value = true
  try {
    gathering.value = await finishGathering(props.excursionId)
    await retry()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    closing.value = false
  }
}

// --- группа выходит к памятному месту ---

const picking = ref(false)
const leading = ref(false)

/** Карту группы видят краевед и те, кто отметился: остальных туда не пустит сервер. */
const mayOpenMap = computed(() => isGuide.value || checkedInAt.value !== null)

function openMap(): void {
  void router.replace({ name: 'excursion-walk', params: { excursionId: props.excursionId } })
}

// Краевед повёл группу — у всех, кто на экране сбора, сама открывается карта.
// Опрос сбора и так идёт каждые четыре секунды, отдельный не нужен.
watch(
  () => gathering.value?.status ?? excursion.value?.status,
  (status) => {
    if (status === 'walking' && mayOpenMap.value) openMap()
  },
)

async function leadGroup(target: WalkTarget): Promise<void> {
  if (leading.value) return
  leading.value = true
  try {
    await leadWalk(props.excursionId, target)
    picking.value = false
    sensor.stop()
    openMap()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    leading.value = false
  }
}

/** Маршрут экскурсии: после сбора краевед ведёт к первой точке одним нажатием. */
const routeStops = computed(() => stopTargets(excursion.value?.stops))
const firstStop = computed(() => nextStop(routeStops.value, null))

/** Откуда считать «ближайшие места»: где краевед сейчас, а без GPS — место сбора. */
const pickFrom = computed(() => position.value ?? (excursion.value ? { lat: excursion.value.lat, lon: excursion.value.lon } : { lat: 52.9686, lon: 36.0694 }))

/** Одна кнопка — три состояния: у краеведа она же открывает сбор. */
const readyLabel = computed(() => {
  if (opening.value) return 'Открываем сбор…'
  return isGuide.value && !isOpen.value ? 'Я на месте — открыть сбор' : 'Приготовиться'
})

/**
 * Куда поведём. Название точки идёт отдельной строкой под подписью кнопки:
 * «Повести к точке 1: …» с длинным названием обрезалось, и краевед нажимал,
 * не зная куда.
 */
const leadHint = computed(() => (firstStop.value ? `Точка 1 · ${firstStop.value.target.name}` : 'Выберите место на карте'))

/** Почему «Повести группу» сейчас нажать нельзя; `null` — можно. */
const leadBlocked = computed(() =>
  (gathering.value?.checked_in_count ?? 0) === 0 ? 'Сначала отметьте хотя бы одного: встряхните телефоны вместе.' : null,
)

</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <AccountRequired v-if="!session.hasAccount" text="Отметиться на экскурсии можно только с аккаунтом." />

    <StateBlock v-else-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="excursion">
      <div class="flex flex-col gap-1">
        <h2 class="font-headline-md text-headline-md text-on-surface">{{ excursion.title }}</h2>
        <p v-if="excursion.place_name" class="flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface-variant">
          <MsIcon name="location_on" :size="16" class="shrink-0" />
          {{ excursion.place_name }}
        </p>
        <p class="font-label-md text-label-md" :class="isOpen ? 'text-primary' : 'text-on-surface-variant'">
          <template v-if="isOpen">Сбор идёт · осталось {{ minutes }} {{ plural(minutes ?? 0, ['минута', 'минуты', 'минут']) }}</template>
          <template v-else-if="excursion.status === 'scheduled'">Сбор ещё не открыт</template>
          <template v-else>Сбор группы закрыт</template>
        </p>
      </div>

      <InlineNotice v-if="!isGuide && !isRegistered">
        Вы не записаны на эту экскурсию — отметиться на месте могут только записавшиеся заранее.
      </InlineNotice>

      <template v-else>
        <!-- Сколько уже в группе -->
        <div class="flex items-center justify-between rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
          <div>
            <p class="font-archival text-archival uppercase text-on-surface-variant">В группе</p>
            <p class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">
              {{ gathering?.checked_in_count ?? excursion.checked_in_count }}
              <span class="font-body-md text-body-md text-on-surface-variant">
                из {{ gathering?.registered_count ?? excursion.registered_count }}
              </span>
            </p>
          </div>
          <span
            v-if="!isGuide && checkedInAt"
            class="inline-flex items-center gap-1 rounded-full bg-secondary-container px-3 py-1.5 font-label-md text-label-md text-on-secondary-container"
          >
            <MsIcon name="task_alt" :size="18" />
            Вы в группе
          </span>
        </div>

        <!-- Подготовка: разрешения только из нажатия -->
        <section
          v-if="phase === 'setup' && excursion.status !== 'finished' && excursion.status !== 'cancelled'"
          class="flex flex-col items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-lg text-center shadow-document"
        >
          <div class="flex h-20 w-20 items-center justify-center rounded-full bg-primary-fixed text-primary">
            <MsIcon name="vibration" :size="40" />
          </div>
          <p class="font-body-md text-body-md text-on-surface">
            {{
              isGuide
                ? 'Откроем сбор, как только убедимся, что вы у места экскурсии. Потом встряхивайте телефон одновременно с каждым участником.'
                : 'Подойдите к краеведу и встряхните телефоны одновременно — так он отметит, что вы пришли.'
            }}
          </p>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Разрешите геолокацию и датчик движения: они нужны, чтобы понять, что вы на месте и трясёте телефон.
          </p>
          <button
            type="button"
            class="mt-space-xs flex min-h-12 w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
            :disabled="opening"
            @click="getReady"
          >
            <MsIcon :name="opening ? 'progress_activity' : 'sensors'" :size="20" :class="{ 'animate-spin': opening }" />
            {{ readyLabel }}
          </button>
        </section>

        <!-- Тряска -->
        <BumpPad
          v-else-if="phase === 'active'"
          :intensity="intensity"
          :sending="sending"
          :busy="opening"
          :active="isOpen"
          :headline="padHeadline"
          :sensor-problem="sensorProblem"
          :position="position"
          :gps-problem="geoProblem"
          @shake="sensor.trigger"
        />

        <InlineNotice v-if="notice" :tone="notice.tone">{{ notice.text }}</InlineNotice>

        <!-- Краевед: кто пришёл и закрыть сбор -->
        <section v-if="isGuide && gathering" class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
          <h3 class="font-archival text-archival uppercase text-on-surface-variant">Отметились на месте</h3>
          <p v-if="!gathering.checked_in.length" class="font-body-sm text-body-sm text-on-surface-variant">Пока никого</p>
          <ul v-else class="flex flex-col gap-1">
            <li
              v-for="person in gathering.checked_in"
              :key="person.user_id"
              class="flex items-center justify-between font-body-sm text-body-sm text-on-surface"
            >
              <span class="flex items-center gap-1.5">
                <MsIcon name="task_alt" :size="16" class="text-secondary" />
                {{ participantLabel(person.user_id) }}
              </span>
              <span class="text-outline">{{ formatTime(person.checked_in_at) }}</span>
            </li>
          </ul>

          <!-- Закрыть сбор — действие редкое и обратное главному, поэтому оно под
               списком, а не рядом с «Повести группу»: промахнуться нельзя. -->
          <ConfirmAction
            v-if="gathering.is_open"
            label="Закрыть сбор"
            icon="event_busy"
            tone="neutral"
            warning="Отметиться встряской больше не выйдет. Кто уже в группе — в ней и останется, повести их можно и после закрытия сбора."
            confirm-label="Закрыть сбор"
            :busy="closing"
            @confirm="finish"
          />
        </section>

        <!-- Главное действие краеведа держим под большим пальцем: список
             отметившихся растёт, и кнопка уезжала бы всё ниже. -->
        <div
          v-if="isGuide && gathering?.is_open"
          class="sticky bottom-0 z-10 -mx-margin flex flex-col gap-space-xs border-t border-outline-variant/40 bg-parchment/95 px-margin pb-space-sm pt-space-sm backdrop-blur"
        >
          <button
            type="button"
            class="flex min-h-12 w-full flex-col items-center justify-center rounded-xl bg-primary-container px-space-md py-3 shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-60 short:py-2.5"
            :disabled="leading || leadBlocked !== null"
            @click="firstStop ? leadGroup(firstStop.target) : (picking = true)"
          >
            <span class="flex items-center gap-space-xs font-label-lg text-label-lg uppercase tracking-wide text-white">
              <MsIcon :name="leading ? 'progress_activity' : 'directions_walk'" :size="18" :class="{ 'animate-spin': leading }" />
              Повести группу
            </span>
            <span class="font-label-sm text-label-sm text-white/80">{{ leadHint }}</span>
          </button>
          <button
            v-if="firstStop"
            type="button"
            class="min-h-11 self-center rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
            :disabled="leading || leadBlocked !== null"
            @click="picking = true"
          >
            Начать с другого места
          </button>
          <p v-if="leadBlocked" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ leadBlocked }}</p>
        </div>
      </template>
    </template>

    <TogetherOverlay v-if="together" :title="together.title" :subtitle="together.subtitle" @close="together = null" />

    <DestinationPicker
      v-if="picking"
      :from="pickFrom"
      :stops="routeStops"
      :busy="leading"
      @close="picking = false"
      @pick="leadGroup"
    />
  </div>
</template>
