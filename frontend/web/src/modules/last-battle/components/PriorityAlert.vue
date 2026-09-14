<script setup>
import { ref } from 'vue'

defineProps({
  tag: { type: String, default: 'Срочный полевой запрос' },
  updatedAt: { type: String, default: 'Обновлено 42 мин назад' },
  title: { type: String, default: 'Внимание поисковика • В 5 км обнаружено предположительное место боя осени 1941 г.' },
  text: {
    type: String,
    default:
      'Помогите архивистам с верификацией местности: лесной массив у высоты 214 (квадрат А-14). Требуется визуальное обследование воронки и сверка с немецкой аэрофотосъёмкой.',
  },
})

const dismissed = ref(false)
const accepted = ref(false)

function accept() {
  accepted.value = true
}
</script>

<template>
  <section v-if="!dismissed" class="mb-6">
    <div class="relative overflow-hidden rounded-lg bg-surface-container-lowest shadow-md p-5 md:p-6 transition-all hover:shadow-xl">
      <div class="absolute -right-16 -top-16 w-64 h-64 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative z-10">
        <div class="flex items-start gap-4">
          <div class="w-12 h-12 rounded-full bg-primary-fixed flex items-center justify-center shrink-0 shadow-sm">
            <span class="material-symbols-outlined text-on-primary-fixed text-[26px]">radar</span>
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full font-label-sm text-label-sm uppercase bg-primary text-on-primary font-bold tracking-wider">
                {{ tag }}
              </span>
              <span class="font-label-sm text-label-sm text-on-surface-variant flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-primary animate-ping" />
                {{ updatedAt }}
              </span>
            </div>
            <h2 class="font-headline-sm text-headline-sm text-on-surface font-bold tracking-tight">{{ title }}</h2>
            <p class="font-body-md text-body-md text-on-surface-variant max-w-4xl mt-0.5">{{ text }}</p>
          </div>
        </div>

        <div class="flex items-center gap-3 shrink-0 self-end md:self-center">
          <button
            class="px-5 py-2.5 rounded-full font-label-lg text-label-lg font-bold shadow-md hover:opacity-95 transition-all flex items-center gap-2"
            :class="accepted ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
            :disabled="accepted"
            @click="accept"
          >
            <span class="material-symbols-outlined text-[18px]">{{ accepted ? 'done' : 'travel_explore' }}</span>
            <span>{{ accepted ? 'Координаты в навигаторе' : 'Принять задачу' }}</span>
          </button>
          <button
            class="w-10 h-10 rounded-full bg-surface-container-high hover:bg-surface-container text-on-surface-variant flex items-center justify-center transition-colors"
            @click="dismissed = true"
          >
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>
