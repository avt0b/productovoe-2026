<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

const query = defineModel<string>({ required: true })

/**
 * Голосовой поиск. Полных типов Web Speech API в `lib.dom` нет, поэтому здесь
 * описан только тот кусок, которым пользуемся.
 */
interface SpeechRecognitionLike {
  lang: string
  interimResults: boolean
  maxAlternatives: number
  start(): void
  stop(): void
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

const speech = window as unknown as {
  SpeechRecognition?: SpeechRecognitionCtor
  webkitSpeechRecognition?: SpeechRecognitionCtor
}
/**
 * Браузер распознавания не умеет (так бывает в APK-обёртке) — кнопки просто
 * нет. Кнопка, которая ничего не делает, хуже её отсутствия.
 */
const Recognition = speech.SpeechRecognition ?? speech.webkitSpeechRecognition

const listening = ref(false)
let recognition: SpeechRecognitionLike | null = null

function toggleVoice(): void {
  if (!Recognition) return
  if (listening.value) {
    recognition?.stop()
    return
  }
  recognition = new Recognition()
  recognition.lang = 'ru-RU'
  recognition.interimResults = false
  recognition.maxAlternatives = 1
  recognition.onresult = (event) => {
    const said = event.results[0]?.[0]?.transcript
    if (said) query.value = said
  }
  // Отказали в микрофоне или не расслышали — молча выходим из режима: человек видит, что кнопка погасла.
  recognition.onerror = () => (listening.value = false)
  recognition.onend = () => (listening.value = false)
  listening.value = true
  recognition.start()
}

onBeforeUnmount(() => recognition?.stop())
</script>

<template>
  <div
    class="flex w-full items-center gap-space-sm rounded-full bg-surface-container-lowest px-space-md py-2.5 shadow-document"
  >
    <label class="flex min-w-0 flex-1 items-center gap-space-sm">
      <MsIcon name="search" :size="22" class="text-outline" />
      <span class="sr-only">Поиск по маршрутам</span>
      <input
        v-model="query"
        type="search"
        placeholder="Памятник, дивизия, село…"
        class="w-full border-none bg-transparent p-0 font-body-sm text-body-sm text-on-surface outline-none placeholder:text-outline focus-visible:ring-0 focus-visible:ring-offset-0"
      />
    </label>

    <button
      v-if="query"
      type="button"
      aria-label="Очистить поиск"
      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:text-on-surface"
      @click="query = ''"
    >
      <MsIcon name="close" :size="18" />
    </button>

    <button
      v-if="Recognition"
      type="button"
      :aria-label="listening ? 'Остановить запись' : 'Голосовой поиск'"
      :aria-pressed="listening"
      class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-colors"
      :class="listening ? 'bg-primary text-on-primary' : 'bg-surface-container-low text-on-surface-variant hover:text-primary'"
      @click="toggleVoice"
    >
      <MsIcon :name="listening ? 'graphic_eq' : 'mic'" :size="18" :class="{ 'animate-pulse': listening }" />
    </button>
  </div>
</template>
