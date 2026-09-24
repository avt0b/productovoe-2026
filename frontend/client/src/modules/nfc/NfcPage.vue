<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'

import { errorText } from '@/core/format'
import {
  NfcTagSheet,
  cancelNfcWrite,
  openNfcSettings,
  useNfcScanner,
  writeNfcTag,
  type NfcTag,
} from '@/features/nfc'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'

/** Что записываем на метку. */
type WriteKind = 'app' | 'link' | 'text'

const KINDS: readonly { value: WriteKind; title: string }[] = [
  { value: 'app', title: 'Экран' },
  { value: 'link', title: 'Ссылка' },
  { value: 'text', title: 'Текст' },
]

const HINTS: Record<WriteKind, string> = {
  app: 'marshruty://nfc',
  link: 'https://',
  text: 'Братская могила на площади Мира',
}

const scanner = useNfcScanner((scanned) => (tag.value = scanned))
const tag = ref<NfcTag | null>(null)

const writing = ref(false)
const writeKind = ref<WriteKind>('app')
const writeValue = ref(HINTS.app)
const writeNotice = ref<{ tone: 'success' | 'error'; text: string } | null>(null)
const writeCard = ref<HTMLElement | null>(null)

const state = computed(() => {
  if (!scanner.available) return { tone: 'info' as const, text: 'NFC работает в приложении на телефоне: в браузере меток нет.' }
  if (!scanner.status.value.supported) return { tone: 'error' as const, text: 'На этом телефоне нет NFC.' }
  if (!scanner.status.value.enabled) return { tone: 'error' as const, text: 'NFC выключен — включите его в настройках телефона.' }
  if (scanner.error.value) return { tone: 'error' as const, text: scanner.error.value }
  return { tone: 'success' as const, text: 'Ждём метку. Приложите её к задней стороне телефона.' }
})

/** Почему записать нельзя — вместо молча выключенной кнопки. */
const writeMissing = computed(() => {
  if (!scanner.available) return 'Записать метку можно только в приложении на телефоне'
  if (!scanner.status.value.enabled) return 'Сначала включите NFC'
  if (!writeValue.value.trim()) return writeKind.value === 'text' ? 'Напишите текст для метки' : 'Укажите адрес'
  return null
})

const kindIndex = computed(() => KINDS.findIndex((kind) => kind.value === writeKind.value))

function pickKind(kind: WriteKind): void {
  writeKind.value = kind
  writeValue.value = HINTS[kind]
}

async function write(): Promise<void> {
  if (writeMissing.value || writing.value) return
  writing.value = true
  writeNotice.value = null
  try {
    const value = writeValue.value.trim()
    // Ссылку кладём адресной записью, текст — текстовой: так метку поймут и другие приложения.
    await writeNfcTag(writeKind.value === 'text' ? { text: value } : { uri: value })
    writeNotice.value = { tone: 'success', text: 'Записали. Приложите метку ещё раз — проверим, что получилось.' }
  } catch (reason) {
    writeNotice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    writing.value = false
  }
}

async function stopWriting(): Promise<void> {
  await cancelNfcWrite()
  writing.value = false
}

/** «Записать на метку» из окна прочитанной метки — ведём к форме записи. */
async function toWrite(): Promise<void> {
  tag.value = null
  await nextTick()
  writeCard.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onBeforeUnmount(() => {
  if (writing.value) void cancelNfcWrite()
})
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm short:gap-space-sm">
    <p class="font-body-sm text-body-sm text-on-surface-variant">
      Метка на табличке у памятника или на точке маршрута: приложил телефон — открылся нужный экран.
    </p>

    <InlineNotice :tone="state.tone" icon="nfc">{{ state.text }}</InlineNotice>

    <div v-if="scanner.available && !scanner.status.value.enabled" class="flex flex-wrap gap-space-xs">
      <button
        type="button"
        class="flex items-center gap-space-xs rounded-full bg-secondary px-space-md py-2 font-label-md text-label-md text-on-secondary active:scale-95"
        @click="openNfcSettings"
      >
        <MsIcon name="settings" :size="18" />
        Открыть настройки NFC
      </button>
      <button
        type="button"
        class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="scanner.refreshStatus"
      >
        <MsIcon name="refresh" :size="18" />
        Проверить
      </button>
    </div>

    <!-- Площадка ожидания метки -->
    <section class="flex flex-col items-center gap-space-sm rounded-2xl bg-surface-container-lowest px-space-md py-space-lg text-center shadow-document short:py-space-md">
      <div class="relative flex h-40 w-40 items-center justify-center short:h-32 short:w-32" aria-hidden="true">
        <span class="absolute inset-0 rounded-full bg-secondary/10" :class="{ 'motion-safe:animate-ping': scanner.scanning.value }" />
        <span class="absolute inset-5 rounded-full bg-secondary/15" />
        <span
          class="relative flex h-24 w-24 items-center justify-center rounded-full transition-colors duration-300 short:h-20 short:w-20"
          :class="scanner.scanning.value ? 'bg-secondary text-on-secondary shadow-float' : 'bg-surface-container-high text-on-surface-variant'"
        >
          <MsIcon name="nfc" :size="28" />
        </span>
      </div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">
        {{ scanner.scanning.value ? 'Слушаем метки' : 'Сканер ждёт' }}
      </p>
      <h2
        class="ribbon-shimmer font-headline-md text-headline-md text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)]"
        role="status"
      >
        {{ writing ? 'Приложите метку для записи' : 'Приложите метку' }}
      </h2>
      <p v-if="scanner.lastTag.value" class="font-body-sm text-body-sm text-on-surface-variant">
        Последняя метка: {{ scanner.lastTag.value.id ?? 'без номера' }}
      </p>
      <button
        v-if="scanner.lastTag.value && !tag"
        type="button"
        class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="tag = scanner.lastTag.value"
      >
        <MsIcon name="visibility" :size="18" />
        Показать, что на ней
      </button>
    </section>

    <!-- Запись своей метки -->
    <section ref="writeCard" class="flex scroll-mt-space-md flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div>
        <p class="font-archival text-archival uppercase text-on-surface-variant">Для табличек и точек маршрута</p>
        <h2 class="font-headline-sm text-headline-sm text-on-surface">Записать метку</h2>
        <p class="font-body-sm text-body-sm text-on-surface-variant">Выберите, что будет на метке, и приложите её к телефону.</p>
      </div>

      <div class="relative grid grid-cols-3 rounded-xl bg-surface-container p-1 text-center" role="radiogroup" aria-label="Что записываем">
        <span
          class="absolute inset-y-1 left-1 w-[calc((100%-8px)/3)] rounded-lg bg-surface-container-lowest shadow-float transition-transform duration-300 ease-out"
          :style="{ transform: `translateX(${kindIndex * 100}%)` }"
          aria-hidden="true"
        />
        <button
          v-for="kind in KINDS"
          :key="kind.value"
          type="button"
          role="radio"
          :aria-checked="writeKind === kind.value"
          class="relative z-10 rounded-lg py-2 font-label-md text-label-md transition-colors duration-200"
          :class="writeKind === kind.value ? 'text-on-surface' : 'text-on-surface-variant'"
          :disabled="writing"
          @click="pickKind(kind.value)"
        >
          {{ kind.title }}
        </button>
      </div>

      <FormInput
        v-model="writeValue"
        :label="writeKind === 'text' ? 'Текст' : 'Адрес'"
        :placeholder="HINTS[writeKind]"
        :maxlength="500"
        :hint="writeKind === 'app' ? 'Например, marshruty://routes/<точка>?route=<маршрут>' : ''"
      />

      <InlineNotice v-if="writeNotice" :tone="writeNotice.tone">{{ writeNotice.text }}</InlineNotice>
      <p v-else-if="writeMissing && !writing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ writeMissing }}</p>

      <button
        v-if="!writing"
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="writeMissing !== null"
        @click="write"
      >
        <MsIcon name="edit" :size="18" />
        <span>Записать на метку</span>
      </button>
      <button
        v-else
        type="button"
        class="flex w-full items-center justify-center gap-space-xs rounded-full bg-surface-container-high py-3 font-label-lg text-label-lg text-on-surface active:scale-[0.99]"
        @click="stopWriting"
      >
        <MsIcon name="progress_activity" :size="18" class="animate-spin" />
        Ждём метку — отменить
      </button>
    </section>

    <NfcTagSheet v-if="tag" :tag="tag" @write="toWrite" @close="tag = null" />
  </div>
</template>
