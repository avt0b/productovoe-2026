<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { geolocationProblem, useGeolocation } from '@/core/geo'
import { listPoi } from '@/core/services/map'
import { useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import RouteStopsEditor from './components/RouteStopsEditor.vue'
import { createExcursion, fetchExcursion, isGuideRole, updateExcursion, type StopDraft } from './data'

type PlaceMode = 'memorial' | 'here'

interface Point {
  lat: number
  lon: number
  poiId: string | null
}

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const { position, status: geoStatus, start: startLocating } = useGeolocation()

/** Экран заводит экскурсию и правит уже заведённую: `/excursions/:id/edit`. */
const excursionId = computed(() => (typeof route.params.excursionId === 'string' ? route.params.excursionId : null))
const editing = computed(() => excursionId.value !== null)

const isGuide = computed(() => session.hasAccount && isGuideRole(session.user?.role))

const title = ref('')
const description = ref('')
const placeName = ref('')
const placeMode = ref<PlaceMode>('memorial')
const memorialId = ref('')
const point = ref<Point | null>(null)
const startsAt = ref(localInput(nextHour()))
/** Время, что стояло в экскурсии до правки: его, даже прошедшее, не отвергаем. */
const savedStartsAt = ref<string | null>(null)
const capacity = ref<number | null>(15)
const stops = ref<StopDraft[]>([])

const saving = ref(false)
const formError = ref<string | null>(null)
const tried = ref(false)

/** Места слоя «ВОВ» — экскурсию удобно ставить у памятника. Сервис не ответил — демо-набор. */
const places = useAsync(async () => (await listPoi()).data)
const placeOptions = computed(() => (places.data.value ?? []).map((poi) => ({ value: poi.id, title: poi.title })))

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

/** `datetime-local` ждёт местное время без пояса. */
function localInput(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

/** Ближайший полный час через час: экскурсию редко заводят «на сейчас». */
function nextHour(): Date {
  const date = new Date(Date.now() + 60 * 60 * 1000)
  date.setMinutes(0, 0, 0)
  return date
}

/** Раньше этого времени выбрать нельзя — минуты, пока заполняют форму, не в счёт. */
const minStart = localInput(new Date())

/** Правим — подставляем то, что уже стоит в экскурсии. */
const loading = ref(editing.value)
if (excursionId.value) {
  void fetchExcursion(excursionId.value, session.hasAccount)
    .then((item) => {
      title.value = item.title
      description.value = item.description
      placeName.value = item.place_name
      point.value = { lat: item.lat, lon: item.lon, poiId: item.poi_id }
      placeMode.value = item.poi_id ? 'memorial' : 'here'
      memorialId.value = item.poi_id ?? ''
      capacity.value = item.capacity
      startsAt.value = localInput(new Date(item.starts_at))
      savedStartsAt.value = startsAt.value
      stops.value = (item.stops ?? []).map((stop) => ({ name: stop.name, lat: stop.lat, lon: stop.lon, poi_id: stop.poi_id, note: stop.note }))
    })
    .catch((reason) => (formError.value = errorText(reason)))
    .finally(() => (loading.value = false))
}

/** Место сбора — там, где стоит краевед: удобно, если экскурсию заводят прямо на месте. */
function useCurrentPosition(): void {
  placeMode.value = 'here'
  memorialId.value = ''
  if (position.value) point.value = { lat: position.value.lat, lon: position.value.lon, poiId: null }
  else startLocating()
}

function useMemorial(): void {
  placeMode.value = 'memorial'
  if (!memorialId.value) point.value = null
}

watch(position, (fix) => {
  if (fix && placeMode.value === 'here') point.value = { lat: fix.lat, lon: fix.lon, poiId: null }
})

watch(memorialId, (id) => {
  const poi = places.data.value?.find((item) => item.id === id)
  if (!poi) return
  placeMode.value = 'memorial'
  point.value = { lat: poi.lat, lon: poi.lon, poiId: poi.id }
  placeName.value = poi.title
})

const start = computed(() => (point.value ? { lat: point.value.lat, lon: point.value.lon, name: placeName.value || 'Место сбора' } : null))
const geoProblem = computed(() => (placeMode.value === 'here' ? geolocationProblem(geoStatus.value) : null))

const missing = computed(() => {
  if (!title.value.trim()) return 'Как называется экскурсия?'
  if (!startsAt.value) return 'Когда начало?'
  if (startsAt.value < minStart && startsAt.value !== savedStartsAt.value) return 'Начало не может быть в прошлом — выберите время позже'
  if ((capacity.value ?? 0) < 1) return 'Сколько человек возьмёте — хотя бы одно место'
  if (!point.value) return 'Выберите место сбора: памятник из списка или там, где вы сейчас'
  const unnamed = stops.value.findIndex((stop) => !stop.name.trim())
  if (unnamed >= 0) return `Назовите точку ${unnamed + 1} маршрута — так её увидит группа`
  return null
})
const shownError = computed(() => formError.value ?? (tried.value ? missing.value : null))

async function submit(): Promise<void> {
  if (saving.value) return
  if (missing.value || !point.value) {
    tried.value = true
    return
  }
  saving.value = true
  formError.value = null
  const draft = {
    title: title.value.trim(),
    description: description.value.trim(),
    place_name: placeName.value.trim(),
    lat: point.value.lat,
    lon: point.value.lon,
    poi_id: point.value.poiId,
    // datetime-local — время телефона без пояса; сервису отдаём UTC.
    starts_at: new Date(startsAt.value).toISOString(),
    capacity: Math.round(capacity.value ?? 1),
    stops: stops.value.map((stop) => ({ ...stop, name: stop.name.trim(), note: stop.note.trim() })),
  }
  try {
    const id = excursionId.value
    const saved = id ? await updateExcursion(id, draft) : await createExcursion(draft)
    await router.replace({ name: 'excursion', params: { excursionId: saved.id } })
  } catch (reason) {
    formError.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <AccountRequired v-if="!session.hasAccount" text="Создавать экскурсии можно только с аккаунтом краеведа." />

    <InlineNotice v-else-if="!isGuide" tone="info">
      Водить экскурсии могут краеведы. Подайте заявку на роль в профиле — её подтверждает администратор платформы.
    </InlineNotice>

    <div v-else-if="loading" class="flex items-center justify-center gap-space-xs py-space-xl font-label-md text-label-md text-on-surface-variant" role="status">
      <MsIcon name="progress_activity" :size="20" class="animate-spin" />
      Загружаем экскурсию…
    </div>

    <form v-else class="flex flex-col gap-space-lg" novalidate @submit.prevent="submit">
      <header class="flex flex-col gap-space-xs">
        <p class="font-archival text-archival uppercase text-on-surface-variant">{{ editing ? 'Правка экскурсии' : 'Экскурсия краеведа' }}</p>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Группа соберётся в одном месте, отметится встряской телефона рядом с вами, а дальше вы поведёте её по маршруту.
        </p>
      </header>

      <section class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <p class="flex items-center gap-space-xs font-archival text-archival uppercase text-on-surface-variant">
          <MsIcon name="history_edu" :size="18" class="text-secondary" />
          Об экскурсии
        </p>
        <FormInput v-model="title" label="Название" icon="badge" :maxlength="255" placeholder="Тропа памяти: площадь Мира" />
        <FormTextarea v-model="description" label="О чём" :rows="3" placeholder="Что увидим, сколько идти, что взять с собой" />
      </section>

      <section class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <p class="flex items-center gap-space-xs font-archival text-archival uppercase text-on-surface-variant">
          <MsIcon name="calendar_month" :size="18" class="text-secondary" />
          Когда и сколько
        </p>
        <div class="grid grid-cols-[1fr_6rem] gap-space-sm">
          <FormInput v-model="startsAt" label="Начало" type="datetime-local" :min="minStart" />
          <FormInput v-model="capacity" label="Мест" type="number" inputmode="numeric" :min="1" :max="500" />
        </div>
      </section>

      <section class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <p class="flex items-center gap-space-xs font-archival text-archival uppercase text-on-surface-variant">
          <MsIcon name="groups" :size="18" class="text-secondary" />
          Место сбора
        </p>
        <!-- Два способа — переключатель, а не две кнопки рядом: выбран всегда один. -->
        <div class="grid grid-cols-2 gap-space-xs" role="radiogroup" aria-label="Где собираемся">
          <button
            v-for="option in [
              { value: 'memorial' as const, title: 'У памятника', icon: 'account_balance' },
              { value: 'here' as const, title: 'Где я сейчас', icon: 'my_location' },
            ]"
            :key="option.value"
            type="button"
            role="radio"
            :aria-checked="placeMode === option.value"
            class="flex items-center justify-center gap-space-xs rounded-full px-space-sm py-2.5 font-label-md text-label-md transition-colors duration-200 active:scale-95"
            :class="placeMode === option.value ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-on-surface'"
            @click="option.value === 'here' ? useCurrentPosition() : useMemorial()"
          >
            <MsIcon
              :name="option.value === 'here' && geoStatus === 'locating' ? 'progress_activity' : option.icon"
              :size="18"
              :class="{ 'animate-spin': option.value === 'here' && geoStatus === 'locating' }"
            />
            {{ option.title }}
          </button>
        </div>
        <FormSelect
          v-if="placeMode === 'memorial'"
          v-model="memorialId"
          label="Памятник со слоя «ВОВ»"
          icon="account_balance"
          :options="placeOptions"
          :placeholder="places.loading.value ? 'Загружаем места…' : 'Выберите место'"
          :disabled="places.loading.value"
        />
        <InlineNotice v-if="geoProblem" tone="error">{{ geoProblem }}</InlineNotice>
        <FormInput v-model="placeName" label="Как найти место" icon="location_on" :maxlength="255" placeholder="У Вечного огня, со стороны улицы Ленина" />
      </section>

      <section class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <p class="flex items-center gap-space-xs font-archival text-archival uppercase text-on-surface-variant">
          <MsIcon name="route" :size="18" class="text-secondary" />
          Маршрут после сбора
        </p>
        <RouteStopsEditor v-model="stops" :start="start" />
      </section>

      <div class="flex flex-col gap-space-sm">
        <InlineNotice v-if="shownError" tone="error">{{ shownError }}</InlineNotice>
        <button
          type="submit"
          class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
          :disabled="saving"
        >
          <MsIcon :name="saving ? 'progress_activity' : 'event_available'" :size="18" :class="{ 'animate-spin': saving }" />
          <span>{{ editing ? 'Сохранить экскурсию' : 'Опубликовать экскурсию' }}</span>
        </button>
      </div>
    </form>
  </div>
</template>
