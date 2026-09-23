<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { createTrip, type Squad, type Trip } from '../data'

/**
 * Набор волонтёров на выезд — сценарий кейса «Командир отряда «Высота» хочет
 * создать заявку на набор 10 волонтёров на завтра». Отсюда и значения по
 * умолчанию: завтра, 10 мест.
 */
const props = defineProps<{ squads: Squad[] }>()

const emit = defineEmits<{ close: []; created: [trip: Trip] }>()

function tomorrow(): string {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  const pad = (value: number): string => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const squadId = ref<string>(props.squads[0]?.id ?? '')
const title = ref('')
const location = ref('')
const startsOn = ref(tomorrow())
const capacity = ref<number | null>(10)
const description = ref('')
const checklist = ref('Резиновые сапоги\nРабочие перчатки\nВода и перекус\nЗаряженный телефон')
const saving = ref(false)
const error = ref<string | null>(null)

const squadOptions = computed(() => props.squads.map((squad) => ({ value: squad.id, title: squad.name })))
const valid = computed(
  () => squadId.value !== '' && title.value.trim().length > 0 && startsOn.value !== '' && (capacity.value ?? 0) >= 1,
)

async function submit(): Promise<void> {
  if (!valid.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    const trip = await createTrip(squadId.value, {
      title: title.value.trim(),
      location: location.value.trim(),
      starts_on: startsOn.value,
      capacity: Math.round(capacity.value ?? 1),
      description: description.value.trim(),
      checklist: checklist.value.trim(),
    })
    emit('created', trip)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Набрать волонтёров на выезд" subtitle="Выезд появится в «Выходных с поисковиком»" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormSelect v-if="squads.length > 1" v-model="squadId" label="Отряд" :options="squadOptions" />
      <FormInput v-model="title" label="Что делаем" :maxlength="255" placeholder="Раскопки у д. Семенково" required />
      <FormInput v-model="location" label="Где сбор" :maxlength="255" placeholder="д. Семенково, у школы" />
      <div class="grid grid-cols-[1fr_6rem] gap-space-sm">
        <FormInput v-model="startsOn" label="Когда" type="date" required />
        <FormInput v-model="capacity" label="Мест" type="number" inputmode="numeric" :min="1" :max="1000" required />
      </div>
      <FormTextarea v-model="description" label="Что ждёт волонтёров" :rows="2" />
      <FormTextarea v-model="checklist" label="Чек-лист новичка" :rows="4" hint="Каждый пункт — с новой строки" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-field py-3.5 font-label-lg text-label-lg text-on-secondary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'campaign'" :size="20" :class="{ 'animate-spin': saving }" />
        Объявить набор
      </button>
    </form>
  </SheetDialog>
</template>
