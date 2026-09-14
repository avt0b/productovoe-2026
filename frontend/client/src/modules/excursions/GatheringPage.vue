<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'

import { useAsync } from '@/core/async'
import { errorText, plural } from '@/core/format'
import { geolocationProblem, useGeolocation } from '@/core/geo'
import { useSessionStore } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import AccountRequired from './components/AccountRequired.vue'
import TogetherOverlay from './components/TogetherOverlay.vue'
import {
  fetchExcursion,
  fetchGathering,
  finishGathering,
  sendBump,
  startGathering,
  toPosition,
  type BumpResult,
  type Gathering,
  type Position,
} from './data'
import { formatTime, minutesLeft, participantLabel } from './format'
import { useShake } from './useShake'

const props = defineProps<{ excursionId: string }>()

/** Как часто обновлять счётчик группы, мс. */
const POLL_MS = 4000
/** Сколько ждать первого фикса GPS перед открытием сбора, мс. */
const FIRST_FIX_TIMEOUT_MS = 20_000
/** Через сколько считать, что датчик движения молчит, мс. */
const SENSOR_SILENCE_MS = 3000

type Notice = { tone: 'info' | 'error' | 'success'; text: string }

const session = useSessionStore()
const { data: excursion, loading, error, retry } = useAsync(() => fetchExcursion(props.excursionId, true))
const { position, status: geoStatus, start: startLocating } = useGeolocation()
const {
  status: shakeStatus,
  intensity,
  sensorAlive,
  start: startShakeSensor,
  stop: stopShakeSensor,
  trigger: shakeByButton,
} = useShake(onShake)

const gathering = shallowRef<Gathering | null>(null)
/** `setup` — ждём нажатия: разрешения на GPS и датчик спрашиваются только из нажатия. */
const phase = ref<'setup' | 'active'>('setup')
const sending = ref(false)
const opening = ref(false)
const confirmingFinish = ref(false)
const sensorSilent = ref(false)
const notice = ref<Notice | null>(null)
const together = ref<{ title: string; subtitle: string } | null>(null)
const now = ref(Date.now())

const isGuide = computed(() => excursion.value?.viewer?.is_guide === true)
const isRegistered = computed(() => excursion.value?.viewer?.registered === true)
const isOpen = computed(() => gathering.value?.is_open ?? excursion.value?.status === 'gathering')
const checkedInAt = computed(() => gathering.value?.my_checked_in_at ?? excursion.value?.viewer?.checked_in_at ?? null)
const minutes = computed(() => minutesLeft(gathering.value?.ends_at ?? excursion.value?.gathering_ends_at ?? null, now.value))
const geoProblem = computed(() => geolocationProblem(geoStatus.value))

const partnerWord = computed(() => (isGuide.value ? 'с участником' : 'с краеведом'))

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
    stopShakeSensor()
    notice.value = { tone: 'info', text: 'Сбор группы закрыт' }
  }
})

async function getReady(): Promise<void> {
  startLocating()
  await startShakeSensor()
  phase.value = 'active'
  silenceTimer = setTimeout(() => (sensorSilent.value = !sensorAlive.value), SENSOR_SILENCE_MS)
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

async function onShake(shakenAt: number): Promise<void> {
  if (sending.value) return
  if (!isOpen.value) {
    notice.value = { tone: 'info', text: isGuide.value ? 'Сначала откройте сбор' : 'Краевед ещё не открыл сбор — подождите' }
    return
  }
  const fix = position.value
  if (!fix) {
    notice.value = { tone: 'info', text: 'Ждём GPS — встряхните ещё раз через пару секунд' }
    return
  }

  sending.value = true
  notice.value = { tone: 'info', text: isGuide.value ? 'Ищем, кто трясёт вместе с вами…' : 'Ищем краеведа…' }
  try {
    const shakenMsAgo = Math.min(5000, Math.max(0, Math.round(performance.now() - shakenAt)))
    showResult(await sendBump(props.excursionId, toPosition(fix), shakenMsAgo))
    await refreshGathering()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    sending.value = false
  }
}

function showResult(result: BumpResult): void {
  if (result.result === 'matched') {
    notice.value = null
    // Число «в группе» из ответа краеведу не берём: отметку ставит запрос участника,
    // и он может сохраниться на долю секунды позже. Счётчик на экране догонит опросом.
    const matched = result.matched_user_ids.length
    together.value = isGuide.value
      ? {
          title: 'Вы вместе!',
          subtitle:
            matched === 1
              ? 'Участник отмечен — он в группе'
              : `Отмечены ${matched} ${plural(matched, ['участник', 'участника', 'участников'])}`,
        }
      : { title: 'Вы вместе!', subtitle: 'Краевед отметил, что вы пришли. Хорошей экскурсии!' }
    return
  }
  if (result.result === 'already_checked_in') {
    notice.value = { tone: 'success', text: 'Вы уже в группе — трясти больше не нужно' }
    return
  }
  notice.value = {
    tone: 'info',
    text: isGuide.value
      ? 'Никто не встряхнул телефон одновременно с вами — попробуйте ещё раз вместе'
      : 'Краевед не встряхнул телефон одновременно с вами — договоритесь и попробуйте ещё раз',
  }
}

async function finish(): Promise<void> {
  try {
    gathering.value = await finishGathering(props.excursionId)
    confirmingFinish.value = false
    await retry()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  }
}

const NOTICE_TONES: Record<Notice['tone'], string> = {
  info: 'bg-surface-container-high text-on-surface-variant',
  error: 'bg-error-container text-on-error-container',
  success: 'bg-secondary-container text-on-secondary-container',
}
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

      <div
        v-if="!isGuide && !isRegistered"
        class="flex items-start gap-space-sm rounded-lg bg-surface-container-low p-space-md"
      >
        <MsIcon name="info" :size="20" class="mt-0.5 shrink-0 text-secondary" />
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Вы не записаны на эту экскурсию — отметиться на месте могут только записавшиеся заранее.
        </p>
      </div>

      <template v-else>
        <!-- Сколько уже в группе -->
        <div class="flex items-center justify-between rounded-lg bg-surface-container-lowest p-space-md shadow-sm">
          <div>
            <p class="font-label-sm text-label-sm uppercase tracking-wide text-outline">В группе</p>
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
          class="flex flex-col items-center gap-space-sm rounded-lg bg-surface-container-lowest p-space-lg text-center shadow-sm"
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
            class="mt-space-xs flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99]"
            @click="getReady"
          >
            <MsIcon name="sensors" :size="20" />
            {{ isGuide && !isOpen ? 'Я на месте — открыть сбор' : 'Приготовиться' }}
          </button>
        </section>

        <!-- Тряска -->
        <section v-else-if="phase === 'active'" class="flex flex-col items-center gap-space-md text-center">
          <div class="relative flex h-56 w-56 items-center justify-center" aria-hidden="true">
            <span
              class="absolute inset-0 rounded-full bg-primary/15 transition-transform duration-100"
              :style="{ transform: `scale(${0.8 + intensity * 0.35})` }"
            />
            <span class="absolute inset-8 rounded-full bg-primary/25" :class="{ 'animate-ping': sending }" />
            <span
              class="relative flex h-32 w-32 items-center justify-center rounded-full shadow-lg"
              :class="isOpen ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-outline'"
            >
              <MsIcon :name="sending || opening ? 'progress_activity' : 'vibration'" :size="56" :class="{ 'animate-spin': sending || opening }" />
            </span>
          </div>

          <p class="font-headline-sm text-headline-sm text-on-surface">
            <template v-if="!isOpen">Ждём открытия сбора</template>
            <template v-else-if="!isGuide && checkedInAt">Вы уже в группе</template>
            <template v-else>Встряхните телефон одновременно {{ partnerWord }}</template>
          </p>

          <p
            v-if="shakeStatus === 'unsupported' || shakeStatus === 'denied' || sensorSilent"
            class="font-body-sm text-body-sm text-on-surface-variant"
          >
            {{
              shakeStatus === 'denied'
                ? 'Доступ к датчику движения запрещён — нажимайте «Встряхнуть» одновременно.'
                : 'Датчик движения не отвечает — нажимайте «Встряхнуть» одновременно.'
            }}
          </p>

          <button
            type="button"
            class="flex items-center gap-1.5 rounded-full bg-secondary-container px-space-lg py-2.5 font-label-lg text-label-lg text-on-secondary-container active:scale-95 disabled:opacity-60"
            :disabled="sending || !isOpen"
            @click="shakeByButton"
          >
            <MsIcon name="touch_app" :size="20" />
            Встряхнуть
          </button>

          <p class="flex items-center gap-1 font-label-sm text-label-sm text-outline">
            <MsIcon name="my_location" :size="14" />
            <template v-if="position">GPS ± {{ Math.round(position.accuracyMeters) }} м</template>
            <template v-else-if="geoProblem">{{ geoProblem }}</template>
            <template v-else>Ищем GPS…</template>
          </p>
        </section>

        <p v-if="notice" class="rounded-DEFAULT px-3 py-2 text-center font-body-sm text-body-sm" :class="NOTICE_TONES[notice.tone]" role="status">
          {{ notice.text }}
        </p>

        <!-- Краевед: кто пришёл и закрыть сбор -->
        <section v-if="isGuide && gathering" class="flex flex-col gap-space-sm rounded-lg bg-surface-container-lowest p-space-md shadow-sm">
          <h3 class="font-label-lg text-label-lg text-on-surface">Отметились на месте</h3>
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

          <template v-if="gathering.is_open">
            <button
              v-if="!confirmingFinish"
              type="button"
              class="self-start font-label-md text-label-md text-error"
              @click="confirmingFinish = true"
            >
              Закрыть сбор
            </button>
            <div v-else class="flex gap-space-sm">
              <button type="button" class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md" @click="confirmingFinish = false">
                Ещё собираем
              </button>
              <button type="button" class="flex-1 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error" @click="finish">
                Закрыть
              </button>
            </div>
          </template>
        </section>
      </template>
    </template>

    <TogetherOverlay v-if="together" :title="together.title" :subtitle="together.subtitle" @close="together = null" />
  </div>
</template>
