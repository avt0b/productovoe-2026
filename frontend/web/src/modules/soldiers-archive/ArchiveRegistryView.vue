<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import DirectionsButton from '@shared/components/DirectionsButton.vue'
import PointReviews from '@shared/components/PointReviews.vue'
import * as api from './api.js'

// «Книга памяти» — та же лента народного архива (archive_service), что и
// «Живая память», отфильтрованная по kind=soldier_card. Публичная ручка
// отдаёт только подтверждённые записи (EntryService.search_public) —
// поэтому счётчики и список ниже честно считают именно то, что реально
// пришло с бэка, без выдумки.
const entries = ref([])
const status = ref('idle') // idle | loading | loaded | error
const query = ref('')
const activeLetter = ref(null)
const expandedId = ref(null)

let searchTimer = null
async function load() {
  status.value = 'loading'
  try {
    entries.value = await api.listSoldierCards({ q: query.value.trim() || undefined })
    status.value = 'loaded'
  } catch {
    status.value = 'error'
  }
}

onMounted(load)
watch(query, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 350)
})

const stats = computed(() => ({
  total: entries.value.length,
  withDate: entries.value.filter((e) => e.event_date || e.date_text).length,
  onMap: entries.value.filter((e) => e.lat != null && e.lon != null).length,
}))

const letters = computed(() => {
  const set = new Set(entries.value.map((e) => (e.title || '').trim()[0]?.toUpperCase()).filter(Boolean))
  return [...set].sort((a, b) => a.localeCompare(b, 'ru'))
})

const filtered = computed(() => {
  if (!activeLetter.value) return entries.value
  return entries.value.filter((e) => (e.title || '').trim()[0]?.toUpperCase() === activeLetter.value)
})

const sorted = computed(() => [...filtered.value].sort((a, b) => (a.title || '').localeCompare(b.title || '', 'ru')))

function toggleLetter(letter) {
  activeLetter.value = activeLetter.value === letter ? null : letter
}

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

function dateLabel(entry) {
  if (entry.date_text) return entry.date_text
  if (entry.event_date) return new Date(entry.event_date).toLocaleDateString('ru-RU')
  return ''
}
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-6">
    <div class="bg-surface-container-lowest rounded-2xl shadow-document p-6 flex flex-col gap-1">
      <span class="font-archival text-archival uppercase text-tertiary">Книга памяти Орловской области</span>
      <h1 class="font-headline-lg text-headline-lg text-on-surface font-bold">Архив бойцов</h1>
      <p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">
        Погибшие и пропавшие без вести в Великую Отечественную. Записи народного архива (archive_service) —
        каждую подтвердил поисковик, краевед или модератор.
      </p>

      <div class="mt-4 flex items-center gap-2.5 bg-surface-container-low rounded-full px-4 h-12">
        <span class="material-symbols-outlined text-on-surface-variant text-[20px]">search</span>
        <input
          v-model="query"
          type="search"
          placeholder="Фамилия, имя, отчество — если знаете, год и место"
          class="flex-1 bg-transparent font-body-md text-body-md text-on-surface outline-none placeholder:text-on-surface-variant"
        />
      </div>

      <div class="mt-4 grid grid-cols-3 gap-4">
        <div class="flex flex-col">
          <span class="font-headline-md text-headline-md text-on-surface font-bold">{{ stats.total }}</span>
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">имён в архиве</span>
        </div>
        <div class="flex flex-col">
          <span class="font-headline-md text-headline-md text-on-surface font-bold">{{ stats.withDate }}</span>
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">известна дата</span>
        </div>
        <div class="flex flex-col">
          <span class="font-headline-md text-headline-md text-on-surface font-bold">{{ stats.onMap }}</span>
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">отмечено на карте</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <div class="lg:col-span-3 flex flex-col gap-4">
        <div class="bg-surface-container-lowest rounded-2xl shadow-document p-4">
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Листать архив</span>
          <div class="mt-2 flex flex-wrap gap-1.5">
            <button
              v-for="letter in letters"
              :key="letter"
              type="button"
              class="w-8 h-8 rounded-full font-label-sm text-label-sm font-bold transition-colors"
              :class="
                activeLetter === letter
                  ? 'bg-primary text-on-primary'
                  : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
              "
              @click="toggleLetter(letter)"
            >
              {{ letter }}
            </button>
          </div>
        </div>
      </div>

      <div class="lg:col-span-9 flex flex-col gap-3">
        <div v-if="status === 'loading'" class="flex items-center gap-2 font-label-md text-label-md text-on-surface-variant py-8 justify-center">
          <span class="material-symbols-outlined animate-spin text-[18px]">sync</span>
          Загружаем архив...
        </div>
        <p v-else-if="status === 'error'" class="font-body-sm text-body-sm text-error text-center py-8">
          Не удалось загрузить архив — archive_service недоступен
        </p>
        <p v-else-if="!sorted.length" class="font-body-sm text-body-sm text-on-surface-variant text-center py-8">
          {{ query ? 'По запросу ничего не нашлось.' : 'Карточек бойцов пока нет — предложите первую в «Живой памяти».' }}
        </p>

        <div
          v-for="entry in sorted"
          :key="entry.id"
          class="bg-surface-container-lowest rounded-2xl shadow-document overflow-hidden"
        >
          <button
            type="button"
            class="w-full text-left p-4 flex items-center justify-between gap-3 hover:bg-surface-container-low transition-colors"
            @click="toggleExpand(entry.id)"
          >
            <div class="flex flex-col min-w-0">
              <span class="font-headline-sm text-headline-sm text-on-surface font-bold truncate">{{ entry.title }}</span>
              <span v-if="dateLabel(entry)" class="font-body-sm text-body-sm text-on-surface-variant">{{ dateLabel(entry) }}</span>
            </div>
            <span class="material-symbols-outlined text-[22px] text-on-surface-variant shrink-0" :class="{ 'rotate-180': expandedId === entry.id }">
              expand_more
            </span>
          </button>

          <div v-if="expandedId === entry.id" class="px-4 pb-4 flex flex-col gap-3 border-t border-surface-container-high pt-4">
            <p v-if="entry.body" class="font-body-md text-body-md text-on-surface [overflow-wrap:anywhere]">{{ entry.body }}</p>
            <DirectionsButton v-if="entry.lat != null && entry.lon != null" :point="entry" />
            <PointReviews :point="entry" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
