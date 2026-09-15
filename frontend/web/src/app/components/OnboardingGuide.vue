<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboarding } from '../composables/useOnboarding.js'

const router = useRouter()
const { showGuide, dismiss } = useOnboarding()

const steps = [
  {
    icon: 'military_tech',
    title: 'Добро пожаловать в «Маршруты победы»',
    text: 'Платформа объединяет семейные маршруты, поисковые отряды и архив памяти в одном месте. Коротко покажем, что где искать — это займёт меньше минуты.',
    path: null,
  },
  {
    icon: 'route',
    title: 'Маршруты',
    text: 'Семейные квест-маршруты с точками на карте, заданиями для детей и AR-подсказками. «Начать маршрут» открывает настоящую карту и отмечает пройденные точки.',
    path: '/routes',
  },
  {
    icon: 'location_searching',
    title: 'Последний бой',
    text: 'Карта мест гибели бойцов с реальными координатами и статусом проверки: обнаружено → подтверждено архивом → останки подняты. Поисковики могут добавлять новые точки.',
    path: '/last-battle',
  },
  {
    icon: 'campaign',
    title: 'Штаб',
    text: 'Новости отряда и запись на ближайший выезд «Выходные с поисковиком» — с чек-листом новичка.',
    path: '/expedition-hq',
  },
  {
    icon: 'volunteer_activism',
    title: 'Сборы',
    text: 'Целевые сборы отрядов на снаряжение и топливо, донат идёт напрямую в казну отряда — плюс заявки школ на экскурсии.',
    path: '/fundraising',
  },
  {
    icon: 'auto_stories',
    title: 'Живая память',
    text: 'Народный архив: любой может предложить событие, краевед подтверждает. Здесь же — заявка на «живое фото» бойца.',
    path: '/living-memory',
  },
  {
    icon: 'manage_accounts',
    title: 'Профиль',
    text: 'Личные данные, роль в сообществе и настройки гео-оповещений — доступны после входа в аккаунт.',
    path: '/profile',
  },
]

const index = ref(0)
const isLast = () => index.value === steps.length - 1

function next() {
  if (isLast()) {
    finish()
    return
  }
  index.value += 1
}

function prev() {
  if (index.value > 0) index.value -= 1
}

function finish() {
  const target = steps[index.value]?.path
  dismiss()
  if (target) router.push(target)
}

function skip() {
  dismiss()
}
</script>

<template>
  <div
    v-if="showGuide"
    class="fixed inset-0 z-[60] bg-on-background/50 backdrop-blur-sm flex items-center justify-center p-4"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-lg w-full shadow-2xl flex flex-col overflow-hidden">
      <div class="bg-secondary text-on-secondary p-6 relative overflow-hidden">
        <div class="absolute -right-16 -top-16 w-56 h-56 rounded-full bg-secondary-fixed/10 blur-3xl pointer-events-none" />
        <button
          class="absolute top-4 right-4 font-label-sm text-label-sm text-secondary-fixed-dim hover:text-on-secondary font-bold transition-colors z-10"
          @click="skip"
        >
          Пропустить
        </button>
        <div class="relative z-10 flex flex-col items-center text-center gap-3 pt-2">
          <div class="w-14 h-14 rounded-full bg-primary flex items-center justify-center shadow-md">
            <span class="material-symbols-outlined text-on-primary text-[28px]">{{ steps[index].icon }}</span>
          </div>
          <h2 class="font-headline-md text-headline-md text-on-secondary font-extrabold">{{ steps[index].title }}</h2>
        </div>
      </div>

      <div class="p-6 flex flex-col gap-5">
        <p class="font-body-md text-body-md text-on-surface-variant text-center">{{ steps[index].text }}</p>

        <div class="flex items-center justify-center gap-2">
          <span
            v-for="(step, i) in steps"
            :key="step.title"
            class="h-2 rounded-full transition-all"
            :class="i === index ? 'w-6 bg-primary' : 'w-2 bg-surface-container-high'"
          />
        </div>

        <div class="flex items-center justify-between gap-3">
          <button
            class="px-4 py-2.5 rounded-full font-label-md text-label-md font-bold text-on-surface-variant hover:bg-surface-container-low transition-colors"
            :class="{ invisible: index === 0 }"
            @click="prev"
          >
            Назад
          </button>
          <button
            class="px-6 py-2.5 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm hover:opacity-95 transition-all flex items-center gap-2"
            @click="next"
          >
            <span>{{ isLast() ? 'Начать' : 'Далее' }}</span>
            <span class="material-symbols-outlined text-[18px]">{{ isLast() ? 'check' : 'arrow_forward' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
