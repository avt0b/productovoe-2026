<script setup lang="ts">
import { ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

const props = defineProps<{
  points: number
  title: string
  description: string
  acceptedAnswers: string[]
  success: string
  hint: string
}>()

/** `done` — задание выполнено: точку можно засчитать в прогресс маршрута. */
const emit = defineEmits<{ done: [] }>()

type Verdict = 'correct' | 'wrong' | null

const answer = ref('')
const verdict = ref<Verdict>(null)

/**
 * Ответ засчитывается, если в нём есть любой из верных фрагментов. Дети пишут
 * «76 мм», «ЗиС», «пушка зис-3» — строгое сравнение отбраковало бы всё это.
 *
 * Верных ответов нет («постойте минуту в тишине») — поля ввода нет, задание
 * отмечается выполненным кнопкой.
 */
function check(): void {
  const normalized = answer.value.trim().toLowerCase()
  if (!normalized) return
  verdict.value = props.acceptedAnswers.some((fragment) => normalized.includes(fragment.toLowerCase()))
    ? 'correct'
    : 'wrong'
  if (verdict.value === 'correct') {
    answer.value = ''
    emit('done')
  }
}

function markDone(): void {
  verdict.value = 'correct'
  emit('done')
}
</script>

<template>
  <div class="relative flex flex-col gap-space-sm overflow-hidden rounded-DEFAULT bg-tertiary-fixed/30 p-space-md shadow-sm">
    <div class="flex items-center justify-between">
      <div class="inline-flex items-center gap-1.5 rounded-full bg-tertiary-fixed px-2.5 py-1 font-label-sm text-label-sm text-on-tertiary-fixed">
        <MsIcon name="star" :size="16" filled class="text-tertiary" />
        <span>Квест для всей семьи</span>
      </div>
      <span class="font-label-md text-label-md font-bold text-tertiary">+{{ points }} очков следопыта</span>
    </div>

    <div class="flex flex-col gap-1">
      <h3 class="font-headline-sm text-headline-sm text-on-surface">{{ title }}</h3>
      <p class="font-body-sm text-body-sm text-on-surface-variant">{{ description }}</p>
    </div>

    <button
      v-if="!acceptedAnswers.length && verdict !== 'correct'"
      type="button"
      class="mt-space-xs flex h-11 items-center justify-center gap-1.5 self-start rounded-full bg-tertiary-container px-space-md font-label-md text-label-md text-on-tertiary-container transition-transform active:scale-95"
      @click="markDone"
    >
      <MsIcon name="task_alt" :size="18" />
      Задание выполнено
    </button>

    <form v-if="acceptedAnswers.length" class="flex items-center gap-space-xs pt-space-xs" @submit.prevent="check">
      <label class="relative flex-1">
        <span class="sr-only">Ответ на задание</span>
        <input
          v-model="answer"
          type="text"
          placeholder="Введите ответ или номер..."
          class="h-11 w-full rounded-full bg-surface-container-lowest px-4 font-body-sm text-body-sm text-on-surface placeholder:text-outline focus:outline-none"
        />
      </label>
      <button
        type="submit"
        class="flex h-11 shrink-0 items-center justify-center rounded-full bg-tertiary-container px-space-md font-label-md text-label-md text-on-tertiary-container transition-transform active:scale-95"
      >
        Проверить
      </button>
    </form>

    <div
      v-if="verdict"
      class="flex items-center gap-2 rounded-full px-3 py-2 font-label-md text-label-md"
      :class="verdict === 'correct' ? 'bg-secondary-container text-on-secondary-container' : 'bg-error-container text-on-error-container'"
      role="status"
    >
      <MsIcon :name="verdict === 'correct' ? 'task_alt' : 'error'" :size="18" />
      <span>{{ verdict === 'correct' ? success : hint }}</span>
    </div>
  </div>
</template>
