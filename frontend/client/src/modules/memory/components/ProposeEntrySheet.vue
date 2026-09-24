<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText } from '@/core/format'
import { formatCoordinates, geolocationProblem, useGeolocation } from '@/core/geo'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { ENTRY_KINDS, proposeEntry, updateEntry, type ArchiveEntry, type EntryKind, type NearbyPending } from '../data'
import PhotoPicker from './PhotoPicker.vue'

/**
 * «Предложить событие» — механика народного архива из кейса: запись уходит
 * краеведу на проверку, после подтверждения появляется в общей ленте.
 *
 * `about` — «помочь проверить»: человек знает что-то о неподтверждённой записи
 * рядом. Его рассказ ложится в ту же точку и помогает краеведу решить.
 */
const props = withDefaults(
  defineProps<{
    initialKind?: EntryKind
    about?: NearbyPending | null
    /** Правим свою запись — пока она на проверке. `null` — предлагаем новую. */
    entry?: ArchiveEntry | null
  }>(),
  { initialKind: 'event', about: null, entry: null },
)

const emit = defineEmits<{ close: []; created: [entry: ArchiveEntry] }>()

const HINTS: Record<EntryKind, { title: string; body: string }> = {
  event: { title: 'Бой у деревни Крупышино, октябрь 1941', body: 'Что произошло, кто участвовал, откуда известно' },
  soldier_card: { title: 'Воронов Алексей Григорьевич, 1920 г. р.', body: 'Часть, звание, где воевал, где погиб или пропал, откуда сведения' },
  memory: { title: 'Рассказ бабушки о госпитале в школе', body: 'Как запомнилось, от кого услышано' },
  photo_story: { title: 'Фото роты связистов, 1943', body: 'Кто на снимке, где и когда сделан' },
}

const kinds = Object.keys(ENTRY_KINDS) as EntryKind[]
const aboutPlace = props.about?.lat != null && props.about.lon != null ? { lat: props.about.lat, lon: props.about.lon } : null

const kind = ref<EntryKind>(props.entry?.kind ?? (props.about ? 'memory' : props.initialKind))
const title = ref(props.entry?.title ?? (props.about ? `О записи «${props.about.title}»` : ''))
const body = ref(props.entry?.body ?? '')
const dateText = ref(props.entry?.date_text ?? '')
const mediaUrl = ref(props.entry?.media_url ?? '')
const uploading = ref(false)
const attachPlace = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const { position, status: geoStatus, start: startLocating, stop: stopLocating } = useGeolocation()

watch(attachPlace, (value) => (value ? startLocating() : stopLocating()))

const hint = computed(() => HINTS[kind.value])
const place = computed(() => aboutPlace ?? (attachPlace.value ? position.value : null))
const placeText = computed(() => {
  if (!attachPlace.value) return 'Запись появится на карте рядом с маршрутами'
  if (position.value) return formatCoordinates(position.value)
  return geolocationProblem(geoStatus.value) ?? 'Определяем место…'
})

const missing = computed(() => {
  if (!title.value.trim()) return 'Напишите заголовок'
  if (props.about && !body.value.trim()) return 'Расскажите, что вы знаете и откуда'
  if (uploading.value) return 'Дождитесь, пока фото загрузится'
  if (attachPlace.value && !position.value) return 'Ждём координаты — или выключите привязку к месту'
  return null
})

async function submit(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  const fields = {
    kind: kind.value,
    title: title.value.trim(),
    body: body.value.trim(),
    date_text: dateText.value.trim(),
    media_url: mediaUrl.value || null,
  }
  try {
    // У своей записи место уже стоит — при правке его не трогаем.
    emit(
      'created',
      props.entry
        ? await updateEntry(props.entry.id, fields)
        : await proposeEntry({ ...fields, lat: place.value?.lat ?? null, lon: place.value?.lon ?? null }),
    )
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog
    :title="entry ? 'Изменить запись' : about ? 'Помочь проверить' : 'Предложить в народный архив'"
    :subtitle="
      entry
        ? 'Пока запись на проверке, её можно поправить'
        : about
          ? 'Ваш рассказ увидит краевед, который проверяет запись'
          : 'Краевед проверит и подтвердит запись'
    "
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <div v-if="about" class="flex items-start gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
        <MsIcon :name="ENTRY_KINDS[about.kind].icon" :size="18" class="mt-0.5 shrink-0 text-tertiary" />
        <div class="min-w-0">
          <p class="font-archival text-archival uppercase text-on-surface-variant">Ждёт проверки</p>
          <p class="font-label-md text-label-md text-on-surface">{{ about.title }}</p>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-space-xs" role="radiogroup" aria-label="Что добавляем">
        <button
          v-for="value in kinds"
          :key="value"
          type="button"
          role="radio"
          :aria-checked="kind === value"
          class="flex items-center gap-space-xs rounded-2xl px-space-sm py-2 text-left font-label-md text-label-md transition-colors duration-200 active:scale-95"
          :class="kind === value ? 'bg-secondary-container text-on-secondary-container shadow-document' : 'bg-surface-container-low text-on-surface-variant'"
          @click="kind = value"
        >
          <MsIcon :name="ENTRY_KINDS[value].icon" :size="18" :filled="kind === value" class="shrink-0" />
          <span class="min-w-0 truncate">{{ ENTRY_KINDS[value].title }}</span>
        </button>
      </div>

      <FormInput v-model="title" label="Заголовок" :maxlength="255" :placeholder="hint.title" required />
      <FormTextarea
        v-model="body"
        label="Подробности"
        :rows="4"
        :placeholder="about ? 'Что вы знаете: кто рассказывал, где документ, что видели на месте' : hint.body"
      />
      <FormInput v-model="dateText" label="Когда" :maxlength="120" placeholder="Октябрь 1941 или 12.07.1943" />

      <PhotoPicker v-model="mediaUrl" v-model:uploading="uploading" service="archive" label="Фото или документ" hint="Необязательно, но с документом краевед проверит быстрее." />

      <div v-if="aboutPlace" class="flex items-center gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
        <MsIcon name="pin_drop" :size="18" class="shrink-0 text-secondary" />
        <span class="min-w-0">
          <span class="block font-label-md text-label-md text-on-surface">Там же, где проверяемая запись</span>
          <span class="block font-body-sm text-body-sm text-on-surface-variant">{{ formatCoordinates(aboutPlace) }}</span>
        </span>
      </div>
      <!-- У своей записи место уже стоит: при правке его не двигаем. -->
      <div v-else-if="!entry" class="flex items-center justify-between gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
        <span class="min-w-0">
          <span class="block font-label-md text-label-md text-on-surface">Привязать к месту, где я стою</span>
          <span class="block font-body-sm text-body-sm text-on-surface-variant">{{ placeText }}</span>
        </span>
        <ToggleSwitch v-model="attachPlace" label="Привязать к месту, где я стою" />
      </div>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'send'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ entry ? 'Сохранить запись' : 'Отправить краеведу' }}</span>
      </button>
    </form>
  </SheetDialog>
</template>
