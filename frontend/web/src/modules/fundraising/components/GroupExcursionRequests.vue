<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import GuideRatingList from './GuideRatingList.vue'
import { useAuthSession } from '@modules/auth'
import * as fundraisingApi from '../api.js'

const { session } = useAuthSession()

const excursions = ref([])
const loadStatus = ref('loading') // loading | loaded | error

async function load() {
  try {
    excursions.value = await fundraisingApi.listUpcomingExcursions()
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}
onMounted(load)

// search_hq_service не отдаёт отдельный справочник гидов — собираем его из
// guide_id на загруженных экскурсиях (см. GuideRatingList.vue).
const guides = computed(() => {
  const seen = new Map()
  for (const ex of excursions.value) {
    if (!seen.has(ex.guide_id)) seen.set(ex.guide_id, { id: ex.guide_id, label: `Гид экскурсии «${ex.title}»` })
  }
  return [...seen.values()]
})

const form = reactive({ excursionId: '', org: '', groupSize: '' })
const status = ref('idle') // idle | sending | done
const error = ref('')

const selectedExcursion = computed(() => excursions.value.find((e) => e.id === form.excursionId) ?? null)
const freeSeats = computed(() => {
  if (!selectedExcursion.value) return null
  return Math.max(0, selectedExcursion.value.capacity - selectedExcursion.value.registered_count)
})

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
}

async function submit() {
  error.value = ''
  if (session.status !== 'authenticated') {
    error.value = 'Войдите, чтобы отправить заявку от имени школы или клуба'
    return
  }
  if (!form.excursionId) {
    error.value = 'Выберите экскурсию из списка'
    return
  }
  if (!form.org.trim()) {
    error.value = 'Укажите название школы или клуба'
    return
  }
  status.value = 'sending'
  try {
    await fundraisingApi.registerForExcursion(session.accessToken, form.excursionId, {
      organizationName: form.org.trim(),
      groupSize: form.groupSize ? Number(form.groupSize) : 1,
    })
    status.value = 'done'
    form.org = ''
    form.groupSize = ''
    form.excursionId = ''
    await load() // обновить registered_count в селекте
    setTimeout(() => (status.value = 'idle'), 2000)
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось отправить заявку'
  }
}
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-6">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-primary text-[22px]">groups_3</span>
      <div class="flex flex-col">
        <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Заявки школ и клубов на экскурсии</h2>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Групповая запись на уже запланированную экскурсию гида-поисковика или краеведа
        </span>
      </div>
    </div>

    <p
      v-if="loadStatus === 'loaded' && !excursions.length"
      class="font-body-md text-body-md text-on-surface-variant"
    >
      В search_hq_service пока нет запланированных экскурсий — обратитесь в штаб отряда, чтобы её завели
    </p>
    <p v-else-if="loadStatus === 'error'" class="font-body-md text-body-md text-error">
      Не удалось загрузить список экскурсий — search_hq_service недоступен
    </p>

    <div v-else-if="loadStatus === 'loaded'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Экскурсия
          </label>
          <select
            v-model="form.excursionId"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          >
            <option value="">Выберите из списка</option>
            <option v-for="ex in excursions" :key="ex.id" :value="ex.id">
              {{ ex.title }} · {{ formatDate(ex.starts_at) }}
            </option>
          </select>
          <p v-if="selectedExcursion" class="font-body-sm text-body-sm text-on-surface-variant mt-1.5 px-1">
            {{ selectedExcursion.place_name || 'место уточняется' }} · свободно мест: {{ freeSeats }} из
            {{ selectedExcursion.capacity }}
          </p>
        </div>
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Школа или клуб
          </label>
          <input
            v-model="form.org"
            type="text"
            placeholder="Например, школа № 12, г. Орёл"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Размер группы
          </label>
          <input
            v-model="form.groupSize"
            type="number"
            min="1"
            placeholder="15"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

        <button
          type="submit"
          class="mt-1 px-5 py-2.5 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2"
          :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
          :disabled="status === 'sending'"
        >
          <span class="material-symbols-outlined text-[18px]">
            {{ status === 'done' ? 'check_circle' : status === 'sending' ? 'sync' : 'send' }}
          </span>
          <span>{{ status === 'done' ? 'Заявка отправлена' : status === 'sending' ? 'Отправляем...' : 'Отправить заявку' }}</span>
        </button>
      </form>

      <div class="flex flex-col gap-2">
        <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Гиды с рейтингом</span>
        <GuideRatingList :guides="guides" />
      </div>
    </div>
  </div>
</template>
