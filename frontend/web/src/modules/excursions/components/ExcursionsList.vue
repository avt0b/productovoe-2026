<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import GuideRatingList from './GuideRatingList.vue'
import ExcursionRegisterModal from './ExcursionRegisterModal.vue'
import * as excursionsApi from '../api.js'

const { session } = useAuthSession()

const excursions = ref([])
const loadStatus = ref('loading') // loading | loaded | error

async function load() {
  try {
    // С токеном каждая экскурсия вернётся с viewer.registered/viewer.is_guide
    // (search_hq_service/api/schemas/excursion.py) — без этого нельзя честно
    // отличить «уже записан» от «ещё нет» и кнопка звала бы register() снова
    // и снова (бэкенд это не размножает, просто тихо перезаписывает вашу
    // заявку — не то, что должен ожидать человек от повторного клика).
    excursions.value = await excursionsApi.listUpcomingExcursions(session.accessToken)
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}
onMounted(load)
// Следим именно за токеном, а не только за session.status: смена аккаунта
// (выйти → войти другим) меняет accessToken, а статус может на мгновение
// остаться 'authenticated' (или даже не поменяться, если выход/вход прошёл
// без промежуточного 'idle') — и вкладка тогда не перезапросит viewer для
// нового пользователя.
watch(() => session.accessToken, load)

// search_hq_service не отдаёт отдельный справочник гидов — собираем его из
// guide_id на загруженных экскурсиях (см. GuideRatingList.vue).
const guides = computed(() => {
  const seen = new Map()
  for (const ex of excursions.value) {
    if (!seen.has(ex.guide_id)) seen.set(ex.guide_id, { id: ex.guide_id, label: `Гид экскурсии «${ex.title}»` })
  }
  return [...seen.values()]
})

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
}

function freeSeats(ex) {
  return Math.max(0, ex.capacity - ex.registered_count)
}

// Кнопка недоступна, если мест нет, если это ваша собственная экскурсия
// (бэкенд и так отклонит регистрацию гида на свою же — ExcursionService.
// register: "Краевед не записывается на свою экскурсию"), или если вы уже
// записаны: повторный register() бэкенд не размножает, а тихо перезаписывает
// вашу же заявку — лучше явно показать «Вы записаны», чем звать это молча.
function buttonState(ex) {
  if (ex.viewer?.is_guide) return 'own'
  if (ex.viewer?.registered) return 'registered'
  if (freeSeats(ex) === 0) return 'full'
  return 'open'
}

const BUTTON_META = {
  open: { label: 'Записаться', icon: 'how_to_reg', class: 'bg-primary text-on-primary hover:opacity-95' },
  registered: {
    label: 'Вы записаны',
    icon: 'check_circle',
    class: 'bg-secondary-container text-on-secondary-container cursor-default',
  },
  own: { label: 'Ваша экскурсия', icon: 'person', class: 'bg-surface-container text-on-surface-variant cursor-not-allowed' },
  full: { label: 'Мест нет', icon: 'block', class: 'bg-surface-container text-on-surface-variant cursor-not-allowed' },
}

const modalOpen = ref(false)
const selectedExcursion = ref(null)

function openRegister(ex) {
  selectedExcursion.value = ex
  modalOpen.value = true
}

function onRegistered() {
  load() // обновить registered_count в списке
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-5">
      <div class="flex items-center gap-2.5">
        <span class="material-symbols-outlined text-primary text-[22px]">groups_3</span>
        <div class="flex flex-col">
          <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Экскурсии</h2>
          <span class="font-body-sm text-body-sm text-on-surface-variant">
            Запланированные экскурсии с гидами-поисковиками и краеведами — жмите «Записаться» на нужной
          </span>
        </div>
      </div>

      <p v-if="loadStatus === 'loading'" class="font-body-md text-body-md text-on-surface-variant flex items-center gap-2">
        <span class="material-symbols-outlined animate-spin text-[18px]">sync</span>
        Загружаем список...
      </p>
      <p v-else-if="loadStatus === 'error'" class="font-body-md text-body-md text-error">
        Не удалось загрузить список экскурсий — search_hq_service недоступен
      </p>
      <p v-else-if="!excursions.length" class="font-body-md text-body-md text-on-surface-variant">
        В search_hq_service пока нет запланированных экскурсий — обратитесь в штаб отряда, чтобы её завели
      </p>

      <div v-else class="flex flex-col gap-3">
        <div
          v-for="ex in excursions"
          :key="ex.id"
          class="bg-surface-container-low rounded-DEFAULT p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div class="flex flex-col gap-1 min-w-0">
            <span class="font-label-lg text-label-lg text-on-surface font-bold">{{ ex.title }}</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[15px]">pin_drop</span>
              {{ ex.place_name || 'место уточняется' }}
            </span>
            <span class="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[15px]">event</span>
              {{ formatDate(ex.starts_at) }}
            </span>
            <p v-if="ex.description" class="font-body-sm text-body-sm text-on-surface-variant mt-1">
              {{ ex.description }}
            </p>
            <span class="font-label-sm text-label-sm text-on-surface-variant mt-1">
              Свободно мест: {{ freeSeats(ex) }} из {{ ex.capacity }}
            </span>
          </div>

          <button
            type="button"
            class="shrink-0 px-5 py-2.5 rounded-full font-label-md text-label-md font-bold shadow-sm flex items-center justify-center gap-2 transition-all"
            :class="BUTTON_META[buttonState(ex)].class"
            :disabled="buttonState(ex) !== 'open'"
            @click="openRegister(ex)"
          >
            <span class="material-symbols-outlined text-[18px]">{{ BUTTON_META[buttonState(ex)].icon }}</span>
            {{ BUTTON_META[buttonState(ex)].label }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="guides.length" class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-2">
      <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Гиды с рейтингом</span>
      <GuideRatingList :guides="guides" />
    </div>

    <ExcursionRegisterModal v-model="modalOpen" :excursion="selectedExcursion" @registered="onRegistered" />
  </div>
</template>
