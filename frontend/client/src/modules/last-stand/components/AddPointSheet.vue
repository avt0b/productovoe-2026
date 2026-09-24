<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText } from '@/core/format'
import { formatCoordinates, geolocationProblem, useGeolocation, type GeoMarker, type LatLon } from '@/core/geo'
import GeoMap from '@/ui/geo/GeoMap.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { createPoint, deletePoint, emptySource, formatSource, updatePoint, type FindRecord, type SourceDraft } from '../data'
import SourcePicker from './SourcePicker.vue'

/**
 * Новое место гибели — сценарий кейса: командир отряда «Высота» вносит
 * координаты места гибели десантников 9-й бригады, найденные в экспедиции.
 * Место появляется со статусом «Обнаружено», подтверждает его модератор.
 *
 * Это же окно правит уже отмеченное место: после экспедиции уточняют часть,
 * обстоятельства и координаты. Стадию здесь не трогают — её ведёт модератор.
 */
const props = withDefaults(defineProps<{ record?: FindRecord | null }>(), { record: null })

const emit = defineEmits<{ close: []; created: []; removed: [] }>()

const soldierName = ref(props.record?.raw.soldier_name ?? '')
const unit = ref(props.record?.raw.unit ?? '')
const circumstances = ref(props.record?.raw.circumstances ?? '')
const dateText = ref(props.record?.raw.date_text ?? '')
const source = ref<SourceDraft>(emptySource())
const point = ref<LatLon | null>(props.record ? { lat: props.record.lat, lon: props.record.lon } : null)
const lat = ref<number | null>(props.record?.lat ?? null)
const lon = ref<number | null>(props.record?.lon ?? null)
const saving = ref(false)
const confirmingDelete = ref(false)
const error = ref<string | null>(null)

const { position, status: geoStatus, start: startLocating } = useGeolocation()
let takeMyPosition = false

function useMyPosition(): void {
  takeMyPosition = true
  if (position.value) setPoint(position.value)
  else startLocating()
}

watch(position, (fix) => {
  if (fix && takeMyPosition) {
    takeMyPosition = false
    setPoint(fix)
  }
})

function setPoint(next: LatLon): void {
  // Шесть знаков — около 10 см: точнее GPS всё равно не даст.
  const round = (value: number): number => Math.round(value * 1e6) / 1e6
  point.value = { lat: round(next.lat), lon: round(next.lon) }
  lat.value = point.value.lat
  lon.value = point.value.lon
}

// Координаты ввели руками — ставим точку туда же.
watch([lat, lon], ([nextLat, nextLon]) => {
  if (nextLat === null || nextLon === null) return
  if (Math.abs(nextLat) > 90 || Math.abs(nextLon) > 180) return
  if (point.value?.lat === nextLat && point.value?.lon === nextLon) return
  point.value = { lat: nextLat, lon: nextLon }
})

const markers = computed<GeoMarker[]>(() =>
  point.value ? [{ id: 'new', ...point.value, label: soldierName.value || 'Новое место', icon: 'person_search', tone: 'primary' }] : [],
)
const geoProblem = computed(() => geolocationProblem(geoStatus.value))
const valid = computed(() => point.value !== null && (soldierName.value.trim() || circumstances.value.trim()))

/** Почему кнопка неактивна — вместо молча выключенной кнопки. */
const missing = computed(() => {
  if (!point.value) return 'Поставьте точку на карте или возьмите свои координаты'
  if (!soldierName.value.trim() && !circumstances.value.trim()) return 'Напишите, кто погиб, или обстоятельства — хотя бы одно'
  return null
})

async function submit(): Promise<void> {
  if (!valid.value || saving.value || !point.value) return
  saving.value = true
  error.value = null
  const draft = {
    ...point.value,
    soldier_name: soldierName.value.trim(),
    unit: unit.value.trim(),
    circumstances: circumstances.value.trim(),
    date_text: dateText.value.trim(),
    // При правке источник заполняют заново, только если хотят его заменить:
    // разобрать прежнюю строку обратно на графы нельзя.
    source: formatSource(source.value) || props.record?.raw.source || '',
  }
  try {
    if (props.record) await updatePoint(props.record.id, draft)
    else await createPoint(draft)
    emit('created')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

async function remove(): Promise<void> {
  const record = props.record
  if (!record || saving.value) return
  saving.value = true
  error.value = null
  try {
    await deletePoint(record.id)
    emit('removed')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog
    :title="record ? 'Поправить место' : 'Отметить место гибели'"
    :subtitle="record ? 'Стадию ведёт модератор — здесь уточняют сведения' : 'Появится со статусом «Обнаружено», проверит модератор'"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-lg" @submit.prevent="submit">
      <fieldset class="flex flex-col gap-space-sm">
        <legend class="mb-space-xs font-archival text-archival uppercase text-on-surface-variant">Где</legend>
        <GeoMap
          :selected="point ? 'new' : null"
          :markers="markers"
          :user="position"
          :locating="geoStatus === 'locating'"
          label="Нажмите на карту, чтобы поставить точку"
          class="h-56 w-full rounded-2xl shadow-document short:h-44"
          @pick="setPoint"
          @locate="useMyPosition"
        />
        <button
          type="button"
          class="flex items-center justify-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="useMyPosition"
        >
          <MsIcon
            :name="geoStatus === 'locating' ? 'progress_activity' : 'my_location'"
            :size="18"
            :class="{ 'animate-spin': geoStatus === 'locating' }"
          />
          Я на месте — взять мои координаты
        </button>
        <InlineNotice v-if="geoProblem" tone="error" icon="location_off">{{ geoProblem }}</InlineNotice>
        <div class="grid grid-cols-2 gap-space-sm">
          <FormInput v-model="lat" label="Широта" type="number" inputmode="decimal" step="any" :min="-90" :max="90" />
          <FormInput v-model="lon" label="Долгота" type="number" inputmode="decimal" step="any" :min="-180" :max="180" />
        </div>
        <p v-if="point" class="select-all font-label-md text-label-md text-on-surface-variant">{{ formatCoordinates(point) }}</p>
      </fieldset>

      <fieldset class="flex flex-col gap-space-sm">
        <legend class="mb-space-xs font-archival text-archival uppercase text-on-surface-variant">Кто и когда</legend>
        <FormInput
          v-model="soldierName"
          label="Кто погиб"
          :maxlength="255"
          placeholder="Три неизвестных десантника"
          hint="Если имя неизвестно — так и напишите"
        />
        <FormInput v-model="unit" label="Часть" :maxlength="255" placeholder="9-я воздушно-десантная бригада, 5-й ВДК" />
        <FormTextarea v-model="circumstances" label="Обстоятельства гибели" :rows="3" placeholder="Что нашли, как привязано к местности" />
        <FormInput v-model="dateText" label="Когда" :maxlength="120" placeholder="Октябрь 1941" />
      </fieldset>

      <fieldset class="flex flex-col gap-space-sm">
        <legend class="mb-space-xs font-archival text-archival uppercase text-on-surface-variant">Откуда известно</legend>
        <InlineNotice v-if="record?.raw.source" tone="info">
          Сейчас указано: {{ record.raw.source }}. Заполните графы ниже, только если источник надо заменить.
        </InlineNotice>
        <SourcePicker v-model="source" />
      </fieldset>

      <!-- Ошибка занимает место подсказки, а не встаёт над ней. -->
      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'add_location_alt'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ record ? 'Сохранить' : 'Отметить место' }}</span>
      </button>

      <!-- Убрать место — в два нажатия: точка уже на общей карте, её видят все. -->
      <template v-if="record">
        <button
          type="button"
          class="self-center rounded-full px-space-md py-2 font-label-md text-label-md text-error active:scale-95"
          :aria-expanded="confirmingDelete"
          @click="confirmingDelete = !confirmingDelete"
        >
          Убрать место с карты
        </button>
        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="confirmingDelete ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          :inert="!confirmingDelete"
        >
          <div class="overflow-hidden">
            <div
              class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-low p-space-md"
              role="alertdialog"
              aria-label="Подтверждение удаления места"
            >
              <p class="font-body-sm text-body-sm text-on-surface">
                Убрать место со слоя «ВОВ»? Точка пропадёт с карты у всех. Это не отменить.
              </p>
              <div class="flex gap-space-sm">
                <button
                  type="button"
                  class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
                  @click="confirmingDelete = false"
                >
                  Оставить
                </button>
                <button
                  type="button"
                  class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error active:scale-95 disabled:opacity-60"
                  :disabled="saving"
                  @click="remove"
                >
                  <MsIcon name="delete" :size="18" />
                  Убрать
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </form>
  </SheetDialog>
</template>
