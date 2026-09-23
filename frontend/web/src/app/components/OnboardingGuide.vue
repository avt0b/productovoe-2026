<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useOnboarding } from '../composables/useOnboarding.js'
import { useSidebar } from '../composables/useSidebar.js'

const router = useRouter()
const { showGuide, dismiss } = useOnboarding()
const { isOpen: sidebarOpen } = useSidebar()

const steps = [
  {
    target: null,
    icon: 'military_tech',
    title: 'Добро пожаловать в «Маршруты победы»',
    text: 'Покажем по шагам, где что искать на сайте — займёт меньше минуты. Дальше указатель будет подсвечивать нужный пункт меню слева.',
  },
  {
    target: '/routes',
    icon: 'route',
    title: 'Маршруты',
    text: 'Семейные квест-маршруты с точками на карте и заданиями для детей. «Начать маршрут» открывает настоящую карту.',
  },
  {
    target: '/last-battle',
    icon: 'location_searching',
    title: 'Последний бой',
    text: 'Карта мест гибели бойцов со статусом проверки: обнаружено → подтверждено архивом → останки подняты.',
  },
  {
    target: '/expedition-hq',
    icon: 'campaign',
    title: 'Штаб',
    text: 'Новости отряда и запись на ближайший выезд «Выходные с поисковиком» с чек-листом новичка.',
  },
  {
    target: '/excursions',
    icon: 'groups_3',
    title: 'Запись на экскурсии',
    text: 'Индивидуальная запись или коллективная заявка от школы/клуба на экскурсию с гидом-поисковиком.',
  },
  {
    target: '/fundraising',
    icon: 'volunteer_activism',
    title: 'Сборы',
    text: 'Целевые денежные сборы отрядов на снаряжение и топливо.',
  },
  {
    target: '/living-memory',
    icon: 'auto_stories',
    title: 'Живая память',
    text: 'Народный архив — любой может предложить событие, краевед подтверждает. Здесь же заявка на «живое фото» бойца.',
  },
  {
    target: '/profile',
    icon: 'manage_accounts',
    title: 'Профиль',
    text: 'Личные данные, роль в сообществе и настройки гео-оповещений — доступны после входа в аккаунт.',
  },
]

const index = ref(0)
const rect = ref(null)
const placement = ref('center') // 'right' | 'bottom' | 'center'

const BUBBLE_WIDTH = 336
const GAP = 16

function measure() {
  const step = steps[index.value]
  if (!step.target) {
    rect.value = null
    placement.value = 'center'
    return
  }
  const el = document.querySelector(`[data-tour="nav-${step.target}"]`)
  if (!el) {
    rect.value = null
    placement.value = 'center'
    return
  }
  const r = el.getBoundingClientRect()
  rect.value = { top: r.top, left: r.left, right: r.right, bottom: r.bottom, width: r.width, height: r.height }
  placement.value = r.right + BUBBLE_WIDTH + GAP <= window.innerWidth ? 'right' : 'bottom'
}

async function remeasure() {
  await nextTick()
  measure()
}

watch(index, remeasure)
watch(showGuide, (visible) => {
  if (!visible) return
  sidebarOpen.value = true
  remeasure()
})

function onResize() {
  measure()
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  if (showGuide.value) {
    sidebarOpen.value = true
    remeasure()
  }
})
onUnmounted(() => window.removeEventListener('resize', onResize))

const highlightStyle = computed(() => {
  if (!rect.value) return null
  const pad = 8
  return {
    top: `${rect.value.top - pad}px`,
    left: `${rect.value.left - pad}px`,
    width: `${rect.value.width + pad * 2}px`,
    height: `${rect.value.height + pad * 2}px`,
  }
})

const bubbleStyle = computed(() => {
  if (!rect.value) return null
  if (placement.value === 'right') {
    const top = Math.min(Math.max(rect.value.top - 8, 16), window.innerHeight - 280)
    return { top: `${top}px`, left: `${rect.value.right + GAP}px` }
  }
  const left = Math.min(Math.max(rect.value.left, 16), window.innerWidth - BUBBLE_WIDTH - 16)
  return { top: `${rect.value.bottom + GAP}px`, left: `${left}px` }
})

function isLast() {
  return index.value === steps.length - 1
}

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
  const target = steps[index.value]?.target
  dismiss()
  if (target) router.push(target)
}

function skip() {
  dismiss()
}
</script>

<template>
  <div v-if="showGuide" class="fixed inset-0 z-[60]">
    <!-- Затемнение фона: для центрального шага — сплошное, для шагов с
         указателем — «дырка» создаётся огромной box-shadow у самой рамки -->
    <div v-if="!rect" class="absolute inset-0 bg-on-background/50 backdrop-blur-sm" @click="skip" />
    <div v-else class="absolute inset-0" @click="skip" />

    <!-- Рамка-указатель вокруг пункта меню -->
    <div
      v-if="rect"
      class="fixed rounded-lg border-2 border-primary pointer-events-none transition-all duration-300 ease-out"
      :style="{ ...highlightStyle, boxShadow: '0 0 0 6000px rgba(26,28,30,0.55)' }"
    />

    <!-- Карточка-указатель: скруглённый прямоугольник -->
    <div
      class="fixed w-[336px] max-w-[calc(100vw-32px)] bg-surface-container-lowest rounded-lg shadow-2xl flex flex-col overflow-hidden transition-all duration-300 ease-out"
      :style="
        rect
          ? bubbleStyle
          : { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
      "
      @click.stop
    >
      <div class="bg-secondary text-on-secondary p-5 relative overflow-hidden">
        <div class="absolute -right-10 -top-10 w-36 h-36 rounded-full bg-secondary-fixed/10 blur-2xl pointer-events-none" />
        <button
          class="absolute top-3 right-3 font-label-sm text-label-sm text-secondary-fixed-dim hover:text-on-secondary font-bold transition-colors z-10"
          @click="skip"
        >
          Пропустить
        </button>
        <div class="relative z-10 flex items-center gap-3 pr-16">
          <div class="w-10 h-10 rounded-full bg-primary flex items-center justify-center shadow-md shrink-0">
            <span class="material-symbols-outlined text-on-primary text-[20px]">{{ steps[index].icon }}</span>
          </div>
          <h2 class="font-headline-sm text-headline-sm text-on-secondary font-extrabold leading-tight">
            {{ steps[index].title }}
          </h2>
        </div>
      </div>

      <div class="p-5 flex flex-col gap-4">
        <p class="font-body-sm text-body-sm text-on-surface-variant">{{ steps[index].text }}</p>

        <div class="flex items-center justify-center gap-1.5">
          <span
            v-for="(step, i) in steps"
            :key="step.title"
            class="h-1.5 rounded-full transition-all"
            :class="i === index ? 'w-5 bg-primary' : 'w-1.5 bg-surface-container-high'"
          />
        </div>

        <div class="flex items-center justify-between gap-3">
          <button
            class="px-3.5 py-2 rounded-full font-label-sm text-label-sm font-bold text-on-surface-variant hover:bg-surface-container-low transition-colors"
            :class="{ invisible: index === 0 }"
            @click="prev"
          >
            Назад
          </button>
          <button
            class="px-5 py-2 rounded-full bg-primary text-on-primary font-label-sm text-label-sm font-bold shadow-sm hover:opacity-95 transition-all flex items-center gap-1.5"
            @click="next"
          >
            <span>{{ isLast() ? 'Начать' : 'Далее' }}</span>
            <span class="material-symbols-outlined text-[16px]">{{ isLast() ? 'check' : 'arrow_forward' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
