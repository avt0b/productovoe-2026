<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { usePreferencesStore } from '@/core/preferences'
import { useSessionStore } from '@/core/session'
import { markSeen } from '@/features/onboarding'
import Mascot from '@/ui/Mascot.vue'
import { preloadMascot } from '@/ui/mascot'
import MsIcon from '@/ui/MsIcon.vue'

import ChapterCard from './components/ChapterCard.vue'
import { chaptersFor, flatten, guideChapters, startOf, tabChapters } from './data'

/**
 * Обучение и шпаргалка по разделам — один экран в двух видах.
 *
 * `?tour=1` — обучение по шагам: его предлагает приветствие при первом входе.
 * `?tour=<глава>` — та же лента, но начатая с нужной главы: так из шпаргалки
 * возвращаются за одним разделом, а не листают всё заново. Без `tour` —
 * справочник: главы свёрнутыми карточками.
 *
 * Содержимое зависит от роли и детского режима: поисковику нечего объяснять
 * про заявку на роль, а семье — про проверку находок (см. `data.ts`).
 */
const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const preferences = usePreferencesStore()

const role = computed(() => session.user?.role)
const chapters = computed(() => chaptersFor(role.value, preferences.familyMode))
const entries = computed(() => flatten(chapters.value))

/** Разделы приложения — для шага «где что лежит» и для шпаргалки. */
const sections = computed(() => tabChapters(chapters.value))
const guide = computed(() => guideChapters(chapters.value))

const tourQuery = computed(() => {
  const value = route.query.tour
  return typeof value === 'string' ? value : null
})
const tour = computed(() => tourQuery.value !== null)

const step = ref(0)
const current = computed(() => entries.value[Math.min(step.value, entries.value.length - 1)])
const last = computed(() => step.value >= entries.value.length - 1)

/** Которая это глава по счёту — в подписи над карточкой. */
const chapterNo = computed(() => chapters.value.findIndex((chapter) => chapter.id === current.value.chapter.id) + 1)

/**
 * Первый шаг следующей главы. `-1` — дальше глав нет.
 *
 * Глав девять, и без этой кнопки человеку, которому нужен один раздел,
 * пришлось бы жать «Дальше» три десятка раз или бросить обучение целиком.
 */
const nextChapter = computed(() => {
  const id = current.value.chapter.id
  return entries.value.findIndex((entry, index) => index > step.value && entry.chapter.id !== id)
})

/**
 * Обучение открыли заново или из шпаргалки нужной главой — встаём на её первый
 * шаг. Неизвестная глава (`?tour=1` или мусор в адресе) — с самого начала.
 */
watch(
  tourQuery,
  (value) => {
    if (value === null) return
    const found = value === '1' ? -1 : startOf(entries.value, value)
    step.value = found === -1 ? 0 : found
  },
  { immediate: true },
)

// Картинка следующего шага — заранее: иначе маскот появляется с задержкой
// ровно в тот момент, когда на него смотрят.
watch(
  [step, entries],
  () => {
    const next = entries.value[step.value + 1]
    if (next) preloadMascot(next.step.mascot)
  },
  { immediate: true },
)

/** Модуля раздела может не быть в сборке — тогда ведём только текстом. */
function exists(name: string | null): name is string {
  return name !== null && router.hasRoute(name)
}

function open(name: string): void {
  markSeen()
  if (exists(name)) void router.push({ name })
}

/**
 * Новый шаг читают с начала.
 *
 * Отдельной прокруткой, и обязательно после перерисовки: нажатая кнопка
 * остаётся в фокусе, и WebView, разложив шаг подлиннее, сам подтягивает её
 * обратно в кадр — заголовок шага при этом уезжает за верхний край.
 */
function toStep(index: number): void {
  step.value = index
  void nextTick(() => window.scrollTo({ top: 0 }))
}

function next(): void {
  if (last.value) {
    const action = current.value.step.action
    if (action) return open(action.route)
    return finish()
  }
  toStep(step.value + 1)
}

function back(): void {
  if (step.value === 0) return
  toStep(step.value - 1)
}

function skipChapter(): void {
  if (nextChapter.value === -1) return
  toStep(nextChapter.value)
}

/** Обучение закрыто — дальше шпаргалка: человек уже здесь, незачем его выгонять. */
function finish(): void {
  markSeen()
  void router.replace({ name: 'onboarding' })
}

/** Из шпаргалки — в обучение нужной главой. */
function play(chapterId: string): void {
  void router.replace({ name: 'onboarding', query: { tour: chapterId } })
  window.scrollTo({ top: 0 })
}

/** «Пройти заново» — вся лента с самого начала. */
function restart(): void {
  play('1')
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <!-- Обучение по шагам -->
    <template v-if="tour">
      <div class="flex flex-col gap-space-xs">
        <div class="flex items-baseline justify-between gap-space-sm">
          <p class="min-w-0 truncate font-archival text-archival uppercase text-on-surface-variant">
            Глава {{ chapterNo }} из {{ chapters.length }} · {{ current.chapter.title }}
          </p>
          <p class="shrink-0 font-label-sm text-label-sm text-outline">{{ step + 1 }}/{{ entries.length }}</p>
        </div>
        <!--
          Две полосы: тонкая общая и точки шагов текущей главы. Одной общей мало —
          глав восемь, и без деления кажется, что обучение не кончится никогда.
        -->
        <div
          class="h-1.5 w-full overflow-hidden rounded-full bg-outline-variant"
          role="progressbar"
          :aria-valuenow="step + 1"
          :aria-valuemax="entries.length"
        >
          <div
            class="h-full rounded-full bg-primary transition-[width] duration-300 ease-out"
            :style="{ width: `${((step + 1) / entries.length) * 100}%` }"
          />
        </div>
        <div v-if="current.total > 1" class="flex justify-center gap-1.5 pt-1" aria-hidden="true">
          <span
            v-for="dot in current.total"
            :key="dot"
            class="h-1.5 rounded-full transition-all duration-300"
            :class="dot - 1 === current.index ? 'w-5 bg-secondary' : 'w-1.5 bg-outline-variant'"
          />
        </div>
      </div>

      <section
        class="flex flex-col items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-lg text-center shadow-document short:p-space-md"
      >
        <Mascot :pose="current.step.mascot" :size="176" />
        <p class="flex items-center gap-space-xs font-archival text-archival uppercase text-on-surface-variant">
          <MsIcon :name="current.step.icon" :size="16" />
          {{ current.chapter.title }}
        </p>
        <h2 class="font-headline-md text-headline-md text-on-surface">{{ current.step.title }}</h2>
        <p class="font-body-md text-body-md text-on-surface-variant">{{ current.step.body }}</p>

        <!-- «Что нажать»: то же самое, но руками — по такому списку повторяют, не думая. -->
        <ol v-if="current.step.howto" class="mt-space-xs flex w-full flex-col gap-space-xs text-left">
          <li
            v-for="(line, index) in current.step.howto"
            :key="line"
            class="flex items-start gap-space-sm rounded-xl bg-surface-container-low px-space-sm py-2"
          >
            <span
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-secondary-container font-label-sm text-label-sm text-on-secondary-container"
              aria-hidden="true"
            >
              {{ index + 1 }}
            </span>
            <span class="min-w-0 font-body-sm text-body-sm text-on-surface">{{ line }}</span>
          </li>
        </ol>

        <!-- Шаг «где что лежит»: разделы в том порядке, в каком они нужны этому человеку. -->
        <ul v-if="current.step.sections" class="mt-space-xs flex w-full flex-col gap-space-xs">
          <li
            v-for="section in sections"
            :key="section.id"
            class="flex items-center gap-space-sm rounded-xl bg-surface-container-low px-space-sm py-2 text-left short:py-1.5"
          >
            <span
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container short:h-8 short:w-8"
              aria-hidden="true"
            >
              <MsIcon :name="section.icon" :size="18" />
            </span>
            <span class="min-w-0">
              <span class="block font-label-lg text-label-lg text-on-surface">{{ section.title }}</span>
              <span class="block font-body-sm text-body-sm text-on-surface-variant">{{ section.summary }}</span>
            </span>
          </li>
        </ul>
      </section>

      <div class="flex items-center gap-space-sm">
        <button
          v-if="step > 0"
          type="button"
          aria-label="Назад"
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-surface-container-high text-on-surface transition-colors hover:bg-surface-container-highest active:scale-95 short:h-11 short:w-11"
          @click="back"
        >
          <MsIcon name="arrow_back" :size="20" />
        </button>
        <button
          type="button"
          class="flex min-h-12 flex-1 items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
          @click="next"
        >
          <MsIcon :name="last ? 'arrow_forward' : 'chevron_right'" :size="18" />
          <span>{{ last ? (current.step.action?.label ?? 'Готово') : 'Дальше' }}</span>
        </button>
      </div>
      <div class="flex flex-wrap items-center justify-center gap-x-space-md">
        <button
          v-if="nextChapter !== -1"
          type="button"
          class="min-h-11 rounded-full px-space-sm py-2 font-label-md text-label-md text-on-surface-variant active:scale-95"
          @click="skipChapter"
        >
          Пропустить главу
        </button>
        <button
          type="button"
          class="min-h-11 rounded-full px-space-sm py-2 font-label-md text-label-md text-on-surface-variant active:scale-95"
          @click="finish"
        >
          {{ last ? 'Позже' : 'Пропустить обучение' }}
        </button>
      </div>
    </template>

    <!-- Шпаргалка: сюда возвращаются, когда забылось, где что -->
    <template v-else>
      <div class="flex items-center gap-space-md">
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <p class="font-archival text-archival uppercase text-on-surface-variant">Шпаргалка</p>
          <h2 class="font-headline-md text-headline-md text-on-surface">Что где в приложении</h2>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Раскройте главу, чтобы посмотреть, из чего она состоит, — или пройдите её по шагам.
          </p>
        </div>
        <Mascot pose="explain" :size="104" />
      </div>

      <div class="flex flex-col gap-space-sm">
        <ChapterCard
          v-for="chapter in guide"
          :key="chapter.id"
          :chapter="chapter"
          :openable="exists(chapter.route)"
          @play="play(chapter.id)"
          @open="chapter.route && open(chapter.route)"
        />
      </div>

      <button
        type="button"
        class="min-h-11 self-center rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="restart"
      >
        <span class="flex items-center gap-space-xs">
          <MsIcon name="replay" :size="18" />
          Пройти обучение заново
        </span>
      </button>
    </template>
  </div>
</template>
