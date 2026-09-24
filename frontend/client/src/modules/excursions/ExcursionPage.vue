<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import type { GeoMarker } from '@/core/geo'
import { useSessionStore } from '@/core/session'
import { ChatSheet } from '@/features/chat'
import GeoMap from '@/ui/geo/GeoMap.vue'
import AccountRequired from '@/ui/AccountRequired.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import GuideRatingBadge from './components/GuideRatingBadge.vue'
import ParticipantsList from './components/ParticipantsList.vue'
import RateGuideSheet from './components/RateGuideSheet.vue'
import RegisterSheet from './components/RegisterSheet.vue'
import StatusChip from './components/StatusChip.vue'
import {
  cancelExcursion,
  cancelRegistration,
  fetchExcursion,
  fetchGuideRating,
  fetchParticipants,
  rateExcursion,
  registerForExcursion,
  type GuideRatingSummary,
  type Participant,
  type RegistrationDraft,
} from './data'
import { formatStart } from './format'

const props = defineProps<{ excursionId: string }>()

const router = useRouter()

/** Чат сбора: читать и писать может краевед и тот, кто записался. */
const chatOpen = ref(false)
const session = useSessionStore()

const { data: excursion, loading, error, retry } = useAsync(() =>
  fetchExcursion(props.excursionId, session.hasAccount),
)

/**
 * Как часто записанный участник проверяет, не открыл ли краевед сбор, мс.
 *
 * Раньше экскурсия загружалась один раз: краевед уже стоял на месте, а у
 * участника до перезахода висело «Экскурсия скоро» без кнопки «отметиться».
 * Пять секунд — человек ещё идёт к месту сбора, а кнопка уже появилась.
 */
const WATCH_START_MS = 5000

/** Ждать начала сбора есть смысл только записанному, пока сбор не начался. */
const waitingForGathering = computed(
  () => excursion.value?.status === 'scheduled' && excursion.value.viewer?.registered === true,
)

let watchTimer: ReturnType<typeof setInterval> | undefined

/** Тихое обновление: без «загрузки» на экране — иначе он мигал бы каждые пять секунд. */
async function refreshQuietly(): Promise<void> {
  try {
    excursion.value = await fetchExcursion(props.excursionId, session.hasAccount)
  } catch {
    // Сеть моргнула — попробуем на следующем круге, экран не трогаем.
  }
}

watch(
  waitingForGathering,
  (waiting) => {
    clearInterval(watchTimer)
    watchTimer = waiting ? setInterval(() => void refreshQuietly(), WATCH_START_MS) : undefined
  },
  { immediate: true },
)

onBeforeUnmount(() => clearInterval(watchTimer))

// Рейтинг краеведа и состав группы — дополнение к экскурсии: не загрузились, экран всё равно работает.
watch(
  excursion,
  async (item) => {
    if (!item) return
    try {
      guideRating.value = await fetchGuideRating(item.guide_id)
    } catch {
      guideRating.value = null
    }
    if (!item.viewer?.is_guide) {
      participants.value = []
      return
    }
    try {
      participants.value = await fetchParticipants(item.id)
    } catch {
      participants.value = []
    }
  },
  { immediate: true },
)

const busy = ref(false)
const actionError = ref<string | null>(null)
/** Какое окно открыто поверх экрана: запись группы или оценка краеведа. */
const sheet = ref<'register' | 'rate' | null>(null)
/** Оценку уже отправили — второй раз не предлагаем, хотя сервис и разрешает её менять. */
const rated = ref(false)

/** Средняя оценка краеведа — публичная: по ней выбирают, к кому идти. */
const guideRating = ref<GuideRatingSummary | null>(null)
/** Кто записан. Список отдаётся только ведущему экскурсии. */
const participants = ref<Participant[]>([])
/** Необратимые действия — в два нажатия: первое спрашивает, второе делает. */
const confirming = ref<'unregister' | 'cancel' | null>(null)

/** Кем экскурсия приходится смотрящему. */
const role = computed<'guide' | 'participant' | 'visitor'>(() => {
  const viewer = excursion.value?.viewer
  if (viewer?.is_guide) return 'guide'
  return viewer?.registered ? 'participant' : 'visitor'
})

const seatsLeft = computed(() =>
  excursion.value ? Math.max(0, excursion.value.capacity - excursion.value.registered_count) : 0,
)

const markers = computed<GeoMarker[]>(() => {
  const item = excursion.value
  if (!item) return []
  return [{ id: item.id, lat: item.lat, lon: item.lon, label: item.place_name || item.title, icon: 'groups', tone: 'primary' }]
})

async function act(action: () => Promise<unknown>): Promise<void> {
  if (busy.value) return
  busy.value = true
  actionError.value = null
  try {
    await action()
    confirming.value = null
    await retry()
  } catch (reason) {
    actionError.value = errorText(reason)
  } finally {
    busy.value = false
  }
}

/**
 * Оценить можно только завершённую экскурсию и только тому, кто на ней
 * отметился, — так же проверяет сервис. Показывать кнопку остальным значит
 * обещать то, что закончится ошибкой.
 */
const canRate = computed(
  () =>
    excursion.value?.status === 'finished' &&
    role.value === 'participant' &&
    Boolean(excursion.value?.viewer?.checked_in_at) &&
    !rated.value,
)

async function submitRating(rating: number, comment: string): Promise<void> {
  if (busy.value) return
  busy.value = true
  actionError.value = null
  try {
    await rateExcursion(props.excursionId, rating, comment)
    rated.value = true
    sheet.value = null
    guideRating.value = await fetchGuideRating(excursion.value!.guide_id)
  } catch (reason) {
    actionError.value = errorText(reason)
  } finally {
    busy.value = false
  }
}

async function register(draft: RegistrationDraft | undefined): Promise<void> {
  await act(() => registerForExcursion(props.excursionId, draft))
  if (!actionError.value) sheet.value = null
}

function openGathering(): void {
  void router.push({ name: 'excursion-gathering', params: { excursionId: props.excursionId } })
}

function openWalk(): void {
  void router.push({ name: 'excursion-walk', params: { excursionId: props.excursionId } })
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <StateBlock v-if="loading || error" :loading="loading" :error="error" @retry="retry" />

    <template v-else-if="excursion">
      <div class="flex flex-col gap-space-xs">
        <StatusChip :status="excursion.status" class="self-start" />
        <h2
          class="ribbon-shimmer font-headline-lg-mobile text-headline-lg-mobile text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)]"
        >
          {{ excursion.title }}
        </h2>
        <p class="flex items-center gap-1.5 font-body-md text-body-md text-on-surface-variant">
          <MsIcon name="schedule" :size="18" class="shrink-0 text-secondary" />
          {{ formatStart(excursion.starts_at) }}
        </p>
        <p v-if="excursion.place_name" class="flex items-center gap-1.5 font-body-md text-body-md text-on-surface-variant">
          <MsIcon name="location_on" :size="18" class="shrink-0 text-secondary" />
          {{ excursion.place_name }}
        </p>
      </div>

      <GeoMap :markers="markers" :selected="excursion.id" class="h-44 w-full rounded-2xl shadow-document" />

      <!-- Рейтинг краеведа из ТЗ: по нему выбирают, к кому идти -->
      <GuideRatingBadge :summary="guideRating" />

      <p v-if="excursion.description" class="font-body-md text-body-md leading-relaxed text-on-surface-variant">
        {{ excursion.description }}
      </p>

      <div class="grid grid-cols-2 gap-space-sm">
        <div class="rounded-2xl bg-surface-container-lowest p-space-sm text-center shadow-document">
          <p class="font-headline-md text-headline-md text-on-surface">{{ excursion.registered_count }}</p>
          <p class="font-label-sm text-label-sm text-on-surface-variant">записались из {{ excursion.capacity }}</p>
        </div>
        <div class="rounded-2xl bg-surface-container-lowest p-space-sm text-center shadow-document">
          <p class="font-headline-md text-headline-md text-on-surface">{{ excursion.checked_in_count }}</p>
          <p class="font-label-sm text-label-sm text-on-surface-variant">отметились на месте</p>
        </div>
      </div>

      <!-- Что можно сделать -->
      <section class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <AccountRequired
          v-if="!session.hasAccount"
          text="Записаться на экскурсию и отметиться на месте можно только с аккаунтом."
        />

        <template v-else-if="role === 'guide'">
          <p class="flex items-center gap-1.5 font-label-lg text-label-lg text-on-surface">
            <MsIcon name="record_voice_over" :size="20" class="text-primary" />
            Вы ведёте эту экскурсию
          </p>
          <button
            type="button"
            class="flex items-center justify-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="chatOpen = true"
          >
            <MsIcon name="chat" :size="18" />
            Чат сбора
          </button>
          <button
            v-if="excursion.status === 'scheduled' || excursion.status === 'gathering'"
            type="button"
            class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99]"
            @click="openGathering"
          >
            <MsIcon name="vibration" :size="20" />
            {{ excursion.status === 'gathering' ? 'Открыть сбор группы' : 'Я на месте — начать сбор' }}
          </button>
          <button
            v-if="excursion.status === 'walking'"
            type="button"
            class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99]"
            @click="openWalk"
          >
            <MsIcon name="map" :size="20" />
            Группа идёт — карта
          </button>
          <ParticipantsList v-if="participants.length" :participants="participants" />

          <template v-if="excursion.status === 'scheduled'">
            <button
              type="button"
              class="flex items-center justify-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
              @click="router.push({ name: 'excursion-edit', params: { excursionId: excursion.id } })"
            >
              <MsIcon name="edit" :size="18" />
              Изменить экскурсию
            </button>
            <button
              v-if="confirming !== 'cancel'"
              type="button"
              class="font-label-md text-label-md text-error"
              @click="confirming = 'cancel'"
            >
              Отменить экскурсию
            </button>
            <div v-else class="flex gap-space-sm">
              <button type="button" class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md" @click="confirming = null">
                Не отменять
              </button>
              <button
                type="button"
                class="flex-1 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error disabled:opacity-60"
                :disabled="busy"
                @click="act(() => cancelExcursion(excursion!.id))"
              >
                Отменить
              </button>
            </div>
          </template>
        </template>

        <template v-else-if="role === 'participant'">
          <p class="flex items-center gap-1.5 font-label-lg text-label-lg text-on-surface">
            <MsIcon :name="excursion.viewer?.checked_in_at ? 'task_alt' : 'how_to_reg'" :size="20" class="text-secondary" />
            {{ excursion.viewer?.checked_in_at ? 'Вы в группе — отметились на месте' : 'Вы записаны' }}
          </p>
          <button
            type="button"
            class="flex items-center justify-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="chatOpen = true"
          >
            <MsIcon name="chat" :size="18" />
            Чат сбора
          </button>
          <button
            v-if="excursion.status === 'gathering' && !excursion.viewer?.checked_in_at"
            type="button"
            class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99]"
            @click="openGathering"
          >
            <MsIcon name="vibration" :size="20" />
            Сбор идёт — отметиться
          </button>
          <button
            v-else-if="excursion.status === 'walking' && excursion.viewer?.checked_in_at"
            type="button"
            class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99]"
            @click="openWalk"
          >
            <MsIcon name="map" :size="20" />
            Группа идёт — карта
          </button>
          <p v-else-if="excursion.status === 'scheduled'" class="font-body-sm text-body-sm text-on-surface-variant">
            Когда краевед на месте откроет сбор, встряхните телефон вместе с ним.
          </p>
          <template v-if="excursion.status === 'scheduled'">
            <button
              v-if="confirming !== 'unregister'"
              type="button"
              class="self-start font-label-md text-label-md text-error"
              @click="confirming = 'unregister'"
            >
              Отменить запись
            </button>
            <div v-else class="flex gap-space-sm">
              <button type="button" class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md" @click="confirming = null">
                Остаться
              </button>
              <button
                type="button"
                class="flex-1 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error disabled:opacity-60"
                :disabled="busy"
                @click="act(() => cancelRegistration(excursion!.id))"
              >
                Отписаться
              </button>
            </div>
          </template>
        </template>

        <template v-else>
          <button
            v-if="excursion.status === 'scheduled'"
            type="button"
            class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-60"
            :disabled="busy || seatsLeft === 0"
            @click="sheet = 'register'"
          >
            <MsIcon :name="busy ? 'progress_activity' : 'how_to_reg'" :size="20" :class="{ 'animate-spin': busy }" />
            {{ seatsLeft > 0 ? `Записаться · осталось мест: ${seatsLeft}` : 'Мест нет' }}
          </button>
          <p v-else-if="excursion.status === 'gathering'" class="font-body-sm text-body-sm text-on-surface-variant">
            Запись закрыта: краевед уже собирает группу на месте.
          </p>
        </template>

        <button
          v-if="canRate"
          type="button"
          class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-tertiary py-3.5 font-label-lg text-label-lg text-on-tertiary shadow-float transition-all active:scale-[0.99]"
          @click="sheet = 'rate'"
        >
          <MsIcon name="star" :size="20" filled />
          Оценить экскурсию
        </button>
        <InlineNotice v-else-if="rated" tone="success" icon="star">
          Спасибо за оценку — по ней другие выберут, к кому пойти.
        </InlineNotice>
        <InlineNotice v-else-if="excursion.status === 'finished'" icon="task_alt">Экскурсия завершена.</InlineNotice>
        <InlineNotice v-if="excursion.status === 'cancelled'" icon="event_busy">
          Краевед отменил экскурсию.
        </InlineNotice>

        <InlineNotice v-if="actionError" tone="error">{{ actionError }}</InlineNotice>
      </section>

      <ChatSheet
      v-if="chatOpen && excursion"
      :subject="{ kind: 'excursion', id: excursion.id, title: excursion.title, hostId: excursion.guide_id }"
      @close="chatOpen = false"
    />
    <RegisterSheet
        v-if="sheet === 'register'"
        :seats-left="seatsLeft"
        :busy="busy"
        @close="sheet = null"
        @submit="register"
      />

      <RateGuideSheet v-if="sheet === 'rate'" :busy="busy" @close="sheet = null" @submit="submitRating" />
    </template>
  </div>
</template>
