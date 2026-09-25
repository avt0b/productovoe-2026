<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import DirectionsButton from '@shared/components/DirectionsButton.vue'
import PointReviews from '@shared/components/PointReviews.vue'
import * as api from './api.js'

// «Книга памяти» — та же лента народного архива, что и «Живая память»,
// отфильтрованная по kind=soldier_card. Публичная ручка отдаёт только
// подтверждённые записи. Карточек десятки тысяч, поэтому список листается
// страницами по алфавиту, поиск и буква считаются на сервере, а счётчики и
// алфавит в шапке — сводкой по всему разделу, а не по загруженной странице.
const entries = ref([])
const status = ref('idle') // idle | loading | loaded | error
const query = ref('')
const activeLetter = ref(null)
const expandedId = ref(null)
const summary = ref(null)
const hasMore = ref(false)
const loadingMore = ref(false)

// Ответ на устаревший запрос (буква или поиск уже сменились) не показываем.
let requestId = 0

function filters() {
  return { q: query.value.trim() || undefined, letter: activeLetter.value || undefined }
}

let searchTimer = null
async function load() {
  const current = ++requestId
  status.value = 'loading'
  try {
    const page = await api.listSoldierCards(filters())
    if (current !== requestId) return
    entries.value = page
    hasMore.value = page.length === api.PAGE_SIZE
    status.value = 'loaded'
  } catch {
    if (current === requestId) status.value = 'error'
  }
}

async function loadMore() {
  if (loadingMore.value) return
  const current = requestId
  loadingMore.value = true
  try {
    const page = await api.listSoldierCards({ ...filters(), offset: entries.value.length })
    if (current !== requestId) return
    entries.value = [...entries.value, ...page]
    hasMore.value = page.length === api.PAGE_SIZE
  } catch {
    // Кнопка «Показать ещё» остаётся — можно нажать снова.
  } finally {
    loadingMore.value = false
  }
}

async function loadSummary() {
  try {
    summary.value = await api.soldierCardsSummary()
  } catch {
    summary.value = null
  }
}

onMounted(() => {
  load()
  loadSummary()
})
watch(query, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 350)
})

function count(value) {
  return value == null ? '—' : value.toLocaleString('ru-RU')
}

const stats = computed(() => ({
  total: count(summary.value?.total),
  withDate: count(summary.value?.with_date),
  onMap: count(summary.value?.on_map),
}))

const letters = computed(() => summary.value?.letters ?? [])

function toggleLetter(letter) {
  activeLetter.value = activeLetter.value === letter ? null : letter
  load()
}

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

function dateLabel(entry) {
  if (entry.date_text) return entry.date_text
  if (entry.event_date) return new Date(entry.event_date).toLocaleDateString('ru-RU')
  return ''
}

// Источник анкеты (moypolk.ru и т.п.) зашит текстом в body («Источник: <url>») —
// вытаскиваем ссылку отдельно, чтобы показать её кнопкой, а не куском текста.
const SOURCE_RE = /Источник:\s*(https?:\/\/\S+)/u

function sourceUrl(entry) {
  return entry.body?.match(SOURCE_RE)?.[1] ?? null
}

function bodyWithoutSource(entry) {
  return (entry.body ?? '').replace(SOURCE_RE, '').trim()
}

function excerpt(entry) {
  const text = bodyWithoutSource(entry)
  return text.length > 110 ? `${text.slice(0, 110)}…` : text
}
</script>

<template>
  <div class="flex flex-col w-full pb-16 gap-6">
    <div class="bg-surface-container-lowest rounded-2xl shadow-document p-6 flex flex-col gap-1">
      <span class="font-archival text-archival uppercase text-tertiary">Книга памяти Орловской области</span>
      <h1 class="font-headline-lg text-headline-lg text-on-surface font-bold">Архив бойцов</h1>
      <p class="font-body-md text-body-md text-on-surface-variant max-w-2xl">
        Погибшие и пропавшие без вести в Великую Отечественную. Записи народного архива —
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
          Не удалось загрузить архив — попробуйте позже
        </p>
        <p v-else-if="!entries.length" class="font-body-sm text-body-sm text-on-surface-variant text-center py-8">
          {{ query ? 'По запросу ничего не нашлось.' : 'Карточек бойцов пока нет — предложите первую в «Живой памяти».' }}
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="entry in entries"
            :key="entry.id"
            class="bg-surface-container-lowest rounded-2xl shadow-document overflow-hidden flex flex-col"
          >
            <button
              type="button"
              class="w-full text-left p-4 flex items-start gap-3 hover:bg-surface-container-low transition-colors"
              @click="toggleExpand(entry.id)"
            >
              <img
                v-if="entry.media_url"
                :src="entry.media_url"
                alt=""
                class="w-14 h-14 rounded-full object-cover shrink-0 bg-surface-container-high"
              />
              <div
                v-else
                class="w-14 h-14 rounded-full shrink-0 bg-secondary-container text-on-secondary-container flex items-center justify-center"
              >
                <span class="material-symbols-outlined text-[28px]">military_tech</span>
              </div>

              <div class="flex flex-col min-w-0 flex-1">
                <span class="font-headline-sm text-headline-sm text-on-surface font-bold truncate">{{ entry.title }}</span>
                <span v-if="dateLabel(entry)" class="font-label-sm text-label-sm text-tertiary font-bold">{{ dateLabel(entry) }}</span>
                <p v-if="excerpt(entry)" class="mt-1 font-body-sm text-body-sm text-on-surface-variant line-clamp-2">
                  {{ excerpt(entry) }}
                </p>
                <span v-if="entry.lat != null && entry.lon != null" class="mt-1 flex items-center gap-1 font-label-sm text-label-sm text-on-surface-variant">
                  <span class="material-symbols-outlined text-[14px]">location_on</span>
                  Отмечено на карте
                </span>
              </div>

              <span class="material-symbols-outlined text-[22px] text-on-surface-variant shrink-0" :class="{ 'rotate-180': expandedId === entry.id }">
                expand_more
              </span>
            </button>

            <div v-if="expandedId === entry.id" class="px-4 pb-4 flex flex-col gap-3 border-t border-surface-container-high pt-4">
              <p v-if="bodyWithoutSource(entry)" class="font-body-md text-body-md text-on-surface [overflow-wrap:anywhere]">
                {{ bodyWithoutSource(entry) }}
              </p>
              <a
                v-if="sourceUrl(entry)"
                :href="sourceUrl(entry)"
                target="_blank"
                rel="noopener noreferrer"
                class="self-start flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-surface-container-low font-label-sm text-label-sm font-bold text-on-surface-variant hover:bg-surface-container transition-colors"
              >
                <span class="material-symbols-outlined text-[16px]">open_in_new</span>
                Источник анкеты
              </a>
              <DirectionsButton v-if="entry.lat != null && entry.lon != null" :point="entry" />
              <PointReviews :point="entry" />
            </div>
          </div>
        </div>

        <button
          v-if="status === 'loaded' && hasMore"
          type="button"
          class="self-center mt-2 flex items-center gap-2 px-5 h-11 rounded-full bg-surface-container-low font-label-md text-label-md font-bold text-on-surface hover:bg-surface-container transition-colors disabled:opacity-60"
          :disabled="loadingMore"
          @click="loadMore"
        >
          <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': loadingMore }">
            {{ loadingMore ? 'sync' : 'expand_more' }}
          </span>
          Показать ещё
        </button>
      </div>
    </div>
  </div>
</template>
