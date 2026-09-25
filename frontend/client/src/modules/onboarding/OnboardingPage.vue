<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { usePreferencesStore } from '@/core/preferences'
import { useSessionStore } from '@/core/session'
import { markSeen } from '@/features/onboarding'
import MsIcon from '@/ui/MsIcon.vue'

import SectionCard from './components/SectionCard.vue'
import { linesOf, sectionsFor, tourSteps } from './data'

/**
 * Обучение и шпаргалка по разделам — один экран в двух видах.
 *
 * `?tour=1` — короткое знакомство по шагам: его предлагает приветствие при
 * первом входе. Без него — справочник: шесть свёрнутых карточек, куда можно
 * вернуться из профиля, когда забылось, где что лежит.
 *
 * Тексты зависят от роли и детского режима: поисковику нечего объяснять про
 * заявку на роль, а семье — про проверку находок.
 */
const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const preferences = usePreferencesStore()

const tour = computed(() => route.query.tour === '1')

const role = computed(() => session.user?.role)
const steps = computed(() => tourSteps(role.value, preferences.familyMode))
const sections = computed(() => sectionsFor(role.value))

const step = ref(0)
const current = computed(() => steps.value[Math.min(step.value, steps.value.length - 1)])
const last = computed(() => step.value >= steps.value.length - 1)

// Вышли из обучения и вернулись — начинаем сначала, а не с середины прошлого раза.
watch(tour, (value) => {
  if (value) step.value = 0
})

/** Модуля раздела может не быть в сборке — тогда ведём только текстом. */
function exists(name: string): boolean {
  return router.hasRoute(name)
}

function open(name: string): void {
  markSeen()
  if (exists(name)) void router.push({ name })
}

function next(): void {
  if (last.value) return finish()
  step.value += 1
}

/** Обучение закрыто — дальше справочник: человек уже здесь, незачем его выгонять. */
function finish(): void {
  markSeen()
  void router.replace({ name: 'onboarding' })
}

function restart(): void {
  step.value = 0
  void router.replace({ name: 'onboarding', query: { tour: '1' } })
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <!-- Обучение по шагам -->
    <template v-if="tour">
      <div class="flex justify-center gap-1.5" role="progressbar" :aria-valuenow="step + 1" :aria-valuemax="steps.length">
        <span
          v-for="(item, index) in steps"
          :key="item.title"
          class="h-1.5 rounded-full transition-all duration-300"
          :class="index === step ? 'w-6 bg-primary' : 'w-1.5 bg-outline-variant'"
        />
      </div>

      <section class="flex flex-col items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-lg text-center shadow-document short:p-space-md">
        <span
          class="flex h-20 w-20 items-center justify-center rounded-full bg-primary-fixed text-primary short:h-16 short:w-16"
          aria-hidden="true"
        >
          <MsIcon :name="current.icon" :size="40" />
        </span>
        <p class="font-archival text-archival uppercase text-on-surface-variant">{{ current.rubric }}</p>
        <h2 class="font-headline-md text-headline-md text-on-surface">{{ current.title }}</h2>
        <p class="font-body-md text-body-md text-on-surface-variant">{{ current.body }}</p>

        <!-- Шаг «где что лежит»: разделы списком, в том порядке, в каком они нужны этому человеку. -->
        <ul v-if="current.sections" class="mt-space-xs flex w-full flex-col gap-space-xs">
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

      <button
        type="button"
        class="flex min-h-12 w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="last && current.action ? open(current.action.route) : next()"
      >
        <MsIcon :name="last ? 'arrow_forward' : 'chevron_right'" :size="18" />
        <span>{{ last ? (current.action?.label ?? 'Готово') : 'Дальше' }}</span>
      </button>
      <button
        type="button"
        class="min-h-11 self-center rounded-full px-space-md py-2 font-label-md text-label-md text-on-surface-variant active:scale-95"
        @click="finish"
      >
        {{ last ? 'Позже' : 'Пропустить' }}
      </button>
    </template>

    <!-- Шпаргалка: сюда возвращаются, когда забылось, где что -->
    <template v-else>
      <div class="flex flex-col gap-1">
        <p class="font-archival text-archival uppercase text-on-surface-variant">Шпаргалка</p>
        <h2 class="font-headline-md text-headline-md text-on-surface">Что где в приложении</h2>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Нажмите на раздел, чтобы посмотреть, из чего он состоит.
        </p>
      </div>

      <div class="flex flex-col gap-space-sm">
        <SectionCard
          v-for="section in sections"
          :key="section.id"
          :icon="section.icon"
          :title="section.title"
          :summary="section.summary"
          :lines="linesOf(section, role, preferences.familyMode)"
          :openable="exists(section.route)"
          @open="open(section.route)"
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
