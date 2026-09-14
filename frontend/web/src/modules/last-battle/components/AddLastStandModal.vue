<script setup>
import { reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as lastStandApi from '../api.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'created'])

const { session } = useAuthSession()

const form = reactive({
  soldier_name: '',
  unit: '',
  lat: '',
  lon: '',
  date_text: '',
  circumstances: '',
  source: '',
})
const status = ref('idle')
const error = ref('')

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      status.value = 'idle'
      error.value = ''
    }
  },
)

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  error.value = ''
  const lat = Number(form.lat)
  const lon = Number(form.lon)
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    error.value = 'Укажите координаты числом, например 53.145'
    return
  }
  status.value = 'pending'
  try {
    const point = await lastStandApi.createLastStand(session.accessToken, {
      soldier_name: form.soldier_name,
      unit: form.unit,
      lat,
      lon,
      date_text: form.date_text,
      circumstances: form.circumstances,
      source: form.source,
    })
    emit('created', point)
    status.value = 'done'
    setTimeout(close, 900)
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось сохранить точку'
  }
}
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-lg w-full p-6 shadow-2xl flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[24px]">add_location_alt</span>
          <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold">Новая точка «Последнего боя»</h3>
        </div>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <p class="font-body-sm text-body-sm text-on-surface-variant">
        Запись сразу уходит в map_service со статусом «Обнаружено» — доступна архивистам для проверки.
      </p>

      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <input
          v-model="form.soldier_name"
          type="text"
          placeholder="ФИО бойца (если известно)"
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
        <input
          v-model="form.unit"
          type="text"
          placeholder="Подразделение, например 9-я ВДБр"
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
        <div class="grid grid-cols-2 gap-3">
          <input
            v-model="form.lat"
            type="text"
            inputmode="decimal"
            placeholder="Широта, 53.145"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
          <input
            v-model="form.lon"
            type="text"
            inputmode="decimal"
            placeholder="Долгота, 36.47"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>
        <input
          v-model="form.date_text"
          type="text"
          placeholder="Дата боя текстом, октябрь 1941 г."
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
        <textarea
          v-model="form.circumstances"
          rows="2"
          placeholder="Обстоятельства гибели"
          class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
        />
        <input
          v-model="form.source"
          type="text"
          placeholder="Источник, например Книга Памяти, Т. 5"
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

        <button
          type="submit"
          class="h-11 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2"
          :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
          :disabled="status === 'pending'"
        >
          <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': status === 'pending' }">
            {{ status === 'done' ? 'check_circle' : status === 'pending' ? 'sync' : 'save' }}
          </span>
          <span>{{ status === 'done' ? 'Точка сохранена' : status === 'pending' ? 'Сохраняем...' : 'Сохранить точку' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>
