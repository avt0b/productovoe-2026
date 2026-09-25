<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import { OREL_CENTER, formatCoordinates, useGeolocation, type GeoMarker, type LatLon } from '@/core/geo'
import {
  ROUTE_FILE_MAX_MB,
  addWaypoint,
  updateWaypoint,
  uploadRouteFile,
  type Waypoint,
} from '@/core/services/routes'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

/**
 * Точка маршрута: место на карте, рассказ, детское задание и AR-подсказка —
 * ровно то, что видит семья на экране точки.
 *
 * Эталонный ответ сервис наружу не отдаёт (это спойлер загадки), поэтому при
 * правке поле ответа пустое: заполнили — ответ заменится, оставили пустым —
 * останется прежний.
 */
const props = defineProps<{
  routeId: string
  /** `null` — добавляем новую точку. */
  waypoint: Waypoint | null
  /** Куда ставить точку по умолчанию: центр уже расставленных или Орёл. */
  near: LatLon
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const title = ref(props.waypoint?.title ?? '')
const story = ref(props.waypoint?.story ?? '')
const kidTask = ref(props.waypoint?.kid_task ?? '')
const arHint = ref(props.waypoint?.ar_hint ?? '')
const answer = ref('')
const audioUrl = ref<string | null>(props.waypoint?.audio_url ?? null)
const audioInput = ref<HTMLInputElement | null>(null)
const audioName = ref('')
const uploading = ref(false)
const point = ref<LatLon>(
  props.waypoint ? { lat: props.waypoint.lat, lon: props.waypoint.lon } : { lat: props.near.lat, lon: props.near.lon },
)
const saving = ref(false)
const error = ref<string | null>(null)

const { position, status: geoStatus, start: startLocating } = useGeolocation()
let takeMyPosition = false

function useMyPosition(): void {
  takeMyPosition = true
  if (position.value) setPoint(position.value)
  else startLocating()
}

watch(position, (fix) => {
  if (!fix || !takeMyPosition) return
  takeMyPosition = false
  setPoint(fix)
})

function setPoint(next: LatLon): void {
  // Шесть знаков — около 10 см: точнее GPS всё равно не даст.
  const round = (value: number): number => Math.round(value * 1e6) / 1e6
  point.value = { lat: round(next.lat), lon: round(next.lon) }
}

/** Аудиорассказ на точке — «аудиовоспоминания» и «аудиогид» из ТЗ. */
async function pickAudio(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  error.value = null
  uploading.value = true
  audioName.value = file.name
  try {
    audioUrl.value = await uploadRouteFile(file)
  } catch (reason) {
    audioName.value = ''
    // 503 — хранилище не поднято: точку это не отменяет, аудио добавят позже.
    error.value =
      reason instanceof ApiError && reason.status === 503
        ? 'Хранилище файлов сейчас недоступно. Сохраните точку без аудио — добавите позже.'
        : errorText(reason)
  } finally {
    uploading.value = false
  }
}

function removeAudio(): void {
  audioUrl.value = null
  audioName.value = ''
  error.value = null
}

const markers = computed<GeoMarker[]>(() => [
  { id: 'point', lat: point.value.lat, lon: point.value.lon, label: title.value || 'Точка маршрута', icon: 'flag', tone: 'primary' },
])

const missing = computed(() => {
  if (!title.value.trim()) return 'Назовите точку'
  if (!story.value.trim()) return 'Добавьте рассказ — его читают на месте'
  return null
})

async function save(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  const draft = {
    title: title.value.trim(),
    lat: point.value.lat,
    lon: point.value.lon,
    story: story.value.trim(),
    kid_task: kidTask.value.trim(),
    ar_hint: arHint.value.trim(),
    audio_url: audioUrl.value,
  }
  try {
    if (props.waypoint) {
      // Пустой ответ при правке не трогаем: иначе стёрли бы загадку, которой не видели.
      await updateWaypoint(props.waypoint.id, answer.value.trim() ? { ...draft, expected_answer: answer.value.trim() } : draft)
    } else {
      await addWaypoint(props.routeId, { ...draft, expected_answer: answer.value.trim(), poi_id: null })
    }
    emit('saved')
    emit('close')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog
    :title="waypoint ? 'Точка маршрута' : 'Новая точка'"
    subtitle="Место, рассказ и задание — это и увидит семья на месте"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-md" @submit.prevent="save">
      <GeoMap
        selected="point"
        :markers="markers"
        :center="point ?? OREL_CENTER"
        :user="position"
        :locating="geoStatus === 'locating'"
        label="Нажмите на карту, чтобы поставить точку"
        class="h-48 w-full rounded-2xl shadow-document short:h-40"
        @pick="setPoint"
        @locate="useMyPosition"
      />
      <div class="flex items-center justify-between gap-space-sm">
        <span class="min-w-0 font-body-sm text-body-sm text-on-surface-variant">{{ formatCoordinates(point) }}</span>
        <button
          type="button"
          class="flex shrink-0 items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="useMyPosition"
        >
          <MsIcon name="my_location" :size="18" />
          Я здесь
        </button>
      </div>

      <FormInput v-model="title" label="Название точки" icon="flag" :maxlength="255" placeholder="Сквер Танкистов" required />
      <FormTextarea
        v-model="story"
        label="Рассказ"
        :rows="4"
        :maxlength="4000"
        placeholder="Что здесь было и почему это место важно"
        required
      />
      <FormTextarea
        v-model="kidTask"
        label="Задание для ребёнка"
        :rows="2"
        :maxlength="1000"
        placeholder="Найди на памятнике дату освобождения города"
      />
      <FormInput
        v-model="answer"
        label="Ответ на задание"
        icon="task_alt"
        :maxlength="255"
        :placeholder="waypoint?.has_answer ? 'Ответ задан — впишите новый, чтобы заменить' : '5 августа 1943'"
        hint="Необязательно: без ответа задание просто читают, с ответом — проверяют"
      />
      <div class="flex items-center gap-space-md">
        <span
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant"
          aria-hidden="true"
        >
          <MsIcon :name="uploading ? 'progress_activity' : audioUrl ? 'graphic_eq' : 'volume_up'" :size="22" :class="{ 'animate-spin': uploading }" />
        </span>
        <div class="flex min-w-0 flex-col items-start gap-space-xs">
          <button
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
            :disabled="uploading"
            @click="audioInput?.click()"
          >
            <MsIcon name="upload_file" :size="18" />
            {{ audioUrl ? 'Заменить аудиорассказ' : 'Аудиорассказ' }}
          </button>
          <button
            v-if="audioUrl"
            type="button"
            class="px-space-xs font-label-md text-label-md text-on-surface-variant active:scale-95"
            @click="removeAudio"
          >
            Убрать аудио
          </button>
          <p class="min-w-0 truncate font-body-sm text-body-sm text-on-surface-variant">
            {{ audioName || (audioUrl ? 'Аудио добавлено' : `Необязательно, MP3, OGG, M4A или WAV, до ${ROUTE_FILE_MAX_MB} МБ`) }}
          </p>
        </div>
      </div>
      <input
        ref="audioInput"
        type="file"
        accept="audio/mpeg,audio/ogg,audio/mp4,audio/wav"
        class="sr-only"
        tabindex="-1"
        @change="pickAudio"
      />

      <FormTextarea
        v-model="arHint"
        label="AR-подсказка"
        :rows="2"
        :maxlength="1000"
        placeholder="Наведи камеру на памятник — проводник расскажет о бое"
      />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving || uploading"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'save'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ waypoint ? 'Сохранить точку' : 'Добавить точку' }}</span>
      </button>
    </form>
  </SheetDialog>
</template>
