<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText } from '@/core/format'
import { formatCoordinates, geolocationProblem, useGeolocation } from '@/core/geo'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { ENTRY_KINDS, proposeEntry, type ArchiveEntry, type EntryKind } from '../data'

/**
 * «Предложить событие» — механика народного архива из кейса: запись уходит
 * краеведу на проверку, после подтверждения появляется в общей ленте.
 */
const props = withDefaults(defineProps<{ initialKind?: EntryKind }>(), { initialKind: 'event' })

const emit = defineEmits<{ close: []; created: [entry: ArchiveEntry] }>()

const HINTS: Record<EntryKind, { title: string; body: string }> = {
  event: { title: 'Бой у деревни Крупышино, октябрь 1941', body: 'Что произошло, кто участвовал, откуда известно' },
  soldier_card: { title: 'Воронов Алексей Григорьевич, 1920 г. р.', body: 'Часть, звание, где воевал, где погиб или пропал, откуда сведения' },
  memory: { title: 'Рассказ бабушки о госпитале в школе', body: 'Как запомнилось, от кого услышано' },
  photo_story: { title: 'Фото роты связистов, 1943', body: 'Кто на снимке, где и когда сделан' },
}

const kind = ref<EntryKind | ''>(props.initialKind)
const title = ref('')
const body = ref('')
const dateText = ref('')
const mediaUrl = ref('')
const attachPlace = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const { position, status: geoStatus, start: startLocating, stop: stopLocating } = useGeolocation()

watch(attachPlace, (value) => (value ? startLocating() : stopLocating()))

const kindOptions = (Object.keys(ENTRY_KINDS) as EntryKind[]).map((value) => ({ value, title: ENTRY_KINDS[value].title }))
const hint = computed(() => HINTS[kind.value || 'event'])
const mediaValid = computed(() => !mediaUrl.value.trim() || /^https?:\/\/\S+$/i.test(mediaUrl.value.trim()))
const valid = computed(() => kind.value !== '' && title.value.trim().length > 0 && mediaValid.value && (!attachPlace.value || position.value !== null))

async function submit(): Promise<void> {
  if (!valid.value || saving.value || kind.value === '') return
  saving.value = true
  error.value = null
  try {
    const place = attachPlace.value && position.value ? position.value : null
    const entry = await proposeEntry({
      kind: kind.value,
      title: title.value.trim(),
      body: body.value.trim(),
      date_text: dateText.value.trim(),
      media_url: mediaUrl.value.trim() || null,
      lat: place?.lat ?? null,
      lon: place?.lon ?? null,
    })
    emit('created', entry)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Предложить в народный архив" subtitle="Краевед проверит и подтвердит запись" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormSelect v-model="kind" label="Что добавляем" :options="kindOptions" />
      <FormInput v-model="title" label="Заголовок" :maxlength="255" :placeholder="hint.title" required />
      <FormTextarea v-model="body" label="Подробности" :rows="4" :placeholder="hint.body" />
      <FormInput v-model="dateText" label="Когда" :maxlength="120" placeholder="Октябрь 1941 или 12.07.1943" />
      <FormInput v-model="mediaUrl" label="Ссылка на фото или документ" type="url" inputmode="url" :maxlength="500" placeholder="https://…" />
      <p v-if="!mediaValid" class="font-body-sm text-body-sm text-error" role="alert">Нужна ссылка вида https://…</p>

      <label class="flex cursor-pointer items-center gap-space-sm rounded-DEFAULT bg-surface-container-low p-space-sm">
        <input v-model="attachPlace" type="checkbox" class="h-5 w-5 shrink-0 accent-secondary" />
        <span class="min-w-0 flex-1">
          <span class="block font-label-md text-label-md text-on-surface">Привязать к месту, где я стою</span>
          <span class="block font-body-sm text-body-sm text-on-surface-variant">
            <template v-if="attachPlace && position">{{ formatCoordinates(position) }}</template>
            <template v-else-if="attachPlace">{{ geolocationProblem(geoStatus) ?? 'Определяем место…' }}</template>
            <template v-else>Запись появится на карте рядом с маршрутами</template>
          </span>
        </span>
        <MsIcon v-if="attachPlace && !position" name="progress_activity" :size="18" class="animate-spin text-outline" />
      </label>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'send'" :size="20" :class="{ 'animate-spin': saving }" />
        Отправить краеведу
      </button>
    </form>
  </SheetDialog>
</template>
