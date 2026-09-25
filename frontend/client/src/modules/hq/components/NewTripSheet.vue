<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import ConfirmAction from '@/ui/ConfirmAction.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { cancelTrip, createTrip, deleteTrip, isCancelled, updateTrip, type Squad, type Trip } from '../data'

/**
 * Набор волонтёров на выезд — сценарий кейса «Командир отряда «Высота» хочет
 * создать заявку на набор 10 волонтёров на завтра». Отсюда и значения по
 * умолчанию: завтра, 10 мест.
 *
 * Это же окно правит объявленный выезд: день, места и чек-лист меняются, а
 * отряд остаётся прежним — перевесить выезд на другой сервис не даёт. Отсюда
 * же выезд отменяют (он остаётся в истории, записавшимся приходит
 * уведомление) или удаляют совсем, если объявили по ошибке.
 */
const props = withDefaults(defineProps<{ squads: Squad[]; trip?: Trip | null }>(), { trip: null })

const emit = defineEmits<{ close: []; created: [trip: Trip]; done: [text: string] }>()

function day(offset: number): string {
  const date = new Date()
  date.setDate(date.getDate() + offset)
  const pad = (value: number): string => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** Местная дата, а не UTC: вечером к западу от Гринвича «сегодня» уехало бы на завтра. */
const today = day(0)

const squadId = ref<string>(props.trip?.squad_id ?? props.squads[0]?.id ?? '')
const title = ref(props.trip?.title ?? '')
const location = ref(props.trip?.location ?? '')
const startsOn = ref(props.trip?.starts_on ?? day(1))
const capacity = ref<number | null>(props.trip?.capacity ?? 10)
const description = ref(props.trip?.description ?? '')
const checklist = ref(props.trip?.checklist ?? 'Резиновые сапоги\nРабочие перчатки\nВода и перекус\nЗаряженный телефон')
const saving = ref(false)
const error = ref<string | null>(null)
const cancelReason = ref('')
const cancelled = computed(() => (props.trip ? isCancelled(props.trip) : false))

const squadOptions = computed(() => props.squads.map((squad) => ({ value: squad.id, title: squad.name })))
const missing = computed(() => {
  if (!squadId.value) return 'Выберите отряд'
  if (!title.value.trim()) return 'Напишите, что будем делать'
  if (!startsOn.value) return 'Выберите день выезда'
  // Прошедший день нельзя выбрать заново, но уже прошедший выезд правится как был.
  if (startsOn.value < today && startsOn.value !== props.trip?.starts_on) return 'Выезд не может быть в прошлом — выберите сегодня или позже'
  if ((capacity.value ?? 0) < 1) return 'Сколько человек нужно — хотя бы одно место'
  return null
})

async function submit(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  const draft = {
    title: title.value.trim(),
    location: location.value.trim(),
    starts_on: startsOn.value,
    capacity: Math.round(capacity.value ?? 1),
    description: description.value.trim(),
    checklist: checklist.value.trim(),
  }
  try {
    emit('created', props.trip ? await updateTrip(props.trip.id, draft) : await createTrip(squadId.value, draft))
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

async function act(run: () => Promise<unknown>, text: string): Promise<void> {
  if (saving.value) return
  saving.value = true
  error.value = null
  try {
    await run()
    emit('done', text)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

function cancel(): Promise<void> {
  const trip = props.trip
  if (!trip) return Promise.resolve()
  return act(() => cancelTrip(trip.id, cancelReason.value.trim()), `Выезд «${trip.title}» отменён — записавшиеся получат уведомление`)
}

function remove(): Promise<void> {
  const trip = props.trip
  if (!trip) return Promise.resolve()
  return act(() => deleteTrip(trip.id), `Выезд «${trip.title}» удалён`)
}
</script>

<template>
  <SheetDialog
    :title="trip ? 'Изменить выезд' : 'Набрать волонтёров на выезд'"
    :subtitle="trip ? 'Записавшиеся увидят новые сведения' : 'Выезд появится в «Выходных с поисковиком»'"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <InlineNotice v-if="cancelled" tone="info">Выезд отменён — его можно только удалить.</InlineNotice>
      <FormSelect v-if="!trip && squads.length > 1" v-model="squadId" label="Отряд" :options="squadOptions" />
      <FormInput v-model="title" label="Что делаем" :maxlength="255" placeholder="Раскопки у д. Семенково" required />
      <FormInput v-model="location" label="Где сбор" :maxlength="255" placeholder="д. Семенково, у школы" />
      <div class="grid grid-cols-[1fr_6rem] gap-space-sm">
        <FormInput v-model="startsOn" label="Когда" type="date" :min="trip ? undefined : today" required />
        <FormInput v-model="capacity" label="Мест" type="number" inputmode="numeric" :min="1" :max="1000" required />
      </div>
      <FormTextarea v-model="description" label="Что ждёт волонтёров" :rows="2" />
      <FormTextarea v-model="checklist" label="Чек-лист подготовки" :rows="4" hint="Каждый пункт — с новой строки. Волонтёр отметит, что уже собрал" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving || cancelled"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'campaign'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ trip ? 'Сохранить выезд' : 'Объявить набор' }}</span>
      </button>

      <div v-if="trip" class="flex flex-col gap-space-xs border-t border-outline-variant/40 pt-space-sm">
        <ConfirmAction
          v-if="!cancelled"
          label="Отменить выезд"
          icon="event_busy"
          tone="neutral"
          warning="Выезд останется в истории отряда, запись закроется, а записавшимся придёт уведомление с причиной."
          confirm-label="Отменить"
          :busy="saving"
          @confirm="cancel"
        >
          <FormInput v-model="cancelReason" label="Причина — её увидят волонтёры" :maxlength="500" placeholder="Непогода, перенос на другой день" />
        </ConfirmAction>
        <ConfirmAction
          label="Удалить выезд"
          icon="delete"
          warning="Выезд исчезнет вместе с записями волонтёров и перепиской в чате. Это не отменить."
          confirm-label="Удалить"
          :busy="saving"
          @confirm="remove"
        />
      </div>
    </form>
  </SheetDialog>
</template>
