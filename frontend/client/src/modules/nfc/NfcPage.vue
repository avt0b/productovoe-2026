<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

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
import FormSelect from '@/ui/form/FormSelect.vue'

/** Что записываем на метку. */
type WriteKind = 'app' | 'link' | 'text'

const KINDS: readonly { value: WriteKind; title: string }[] = [
  { value: 'app', title: 'Экран приложения' },
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
const writeKind = ref<WriteKind | ''>('app')
const writeValue = ref(HINTS.app)
const writeNotice = ref<{ tone: 'success' | 'error'; text: string } | null>(null)

const state = computed(() => {
  if (!scanner.available) return { tone: 'info' as const, text: 'NFC работает в приложении на телефоне: в браузере меток нет.' }
  if (!scanner.status.value.supported) return { tone: 'error' as const, text: 'На этом телефоне нет NFC.' }
  if (!scanner.status.value.enabled) return { tone: 'error' as const, text: 'NFC выключен — включите его в настройках телефона.' }
  if (scanner.error.value) return { tone: 'error' as const, text: scanner.error.value }
  return { tone: 'success' as const, text: 'Ждём метку. Приложите её к задней стороне телефона.' }
})

const canWrite = computed(() => scanner.available && scanner.status.value.enabled && writeValue.value.trim().length > 0)

function onKindChange(): void {
  writeValue.value = HINTS[writeKind.value || 'app']
}

async function write(): Promise<void> {
  if (!canWrite.value || writing.value || writeKind.value === '') return
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

onBeforeUnmount(() => {
  if (writing.value) void cancelNfcWrite()
})
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <div class="flex flex-col gap-space-xs">
      <h2 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">NFC-метка</h2>
      <p class="font-body-md text-body-md text-outline">
        Метка на табличке у памятника или на точке маршрута: приложил телефон — открылся нужный экран.
      </p>
    </div>

    <InlineNotice :tone="state.tone === 'success' ? 'success' : state.tone === 'error' ? 'error' : 'info'" icon="nfc">
      {{ state.text }}
    </InlineNotice>

    <div v-if="scanner.available && !scanner.status.value.enabled" class="flex gap-space-sm">
      <button
        type="button"
        class="flex-1 rounded-full bg-primary py-3 font-label-lg text-label-lg text-on-primary active:scale-[0.99]"
        @click="openNfcSettings"
      >
        Открыть настройки NFC
      </button>
      <button
        type="button"
        class="rounded-full bg-surface-container-high px-space-md py-3 font-label-lg text-label-lg text-on-surface"
        @click="scanner.refreshStatus"
      >
        Проверить
      </button>
    </div>

    <!-- Площадка ожидания метки -->
    <section class="flex flex-col items-center gap-space-sm py-space-md text-center">
      <div class="relative flex h-48 w-48 items-center justify-center" aria-hidden="true">
        <span class="absolute inset-0 rounded-full bg-secondary/10" :class="{ 'animate-ping': scanner.scanning.value }" />
        <span class="absolute inset-6 rounded-full bg-secondary/15" />
        <span
          class="relative flex h-28 w-28 items-center justify-center rounded-full shadow-lg"
          :class="scanner.scanning.value ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-outline'"
        >
          <MsIcon name="nfc" :size="52" />
        </span>
      </div>
      <p class="font-headline-sm text-headline-sm text-on-surface">
        {{ writing ? 'Приложите метку для записи' : 'Приложите метку' }}
      </p>
      <p v-if="scanner.lastTag.value" class="font-body-sm text-body-sm text-on-surface-variant">
        Последняя метка: {{ scanner.lastTag.value.id ?? 'без номера' }}
      </p>
      <button
        v-if="scanner.lastTag.value && !tag"
        type="button"
        class="rounded-full bg-secondary-container px-space-md py-2 font-label-md text-label-md text-on-secondary-container"
        @click="tag = scanner.lastTag.value"
      >
        Показать, что на ней
      </button>
    </section>

    <!-- Запись своей метки -->
    <section class="flex flex-col gap-space-sm rounded-lg bg-surface-container-lowest p-space-md shadow-sm">
      <div>
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Записать метку</h3>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Чтобы подготовить табличку: выберите, что на ней будет, и приложите метку.
        </p>
      </div>

      <FormSelect v-model="writeKind" label="Что записываем" :options="KINDS" @update:model-value="onKindChange" />
      <FormInput
        v-model="writeValue"
        :label="writeKind === 'text' ? 'Текст' : 'Адрес'"
        :placeholder="HINTS[writeKind || 'app']"
        :maxlength="500"
        :hint="writeKind === 'app' ? 'Например, marshruty://routes/<точка>?route=<маршрут>' : ''"
      />

      <InlineNotice v-if="writeNotice" :tone="writeNotice.tone">{{ writeNotice.text }}</InlineNotice>

      <button
        v-if="!writing"
        type="button"
        class="flex items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!canWrite"
        @click="write"
      >
        <MsIcon name="edit" :size="20" />
        Записать на метку
      </button>
      <button
        v-else
        type="button"
        class="flex items-center justify-center gap-2 rounded-full bg-surface-container-high py-3.5 font-label-lg text-label-lg text-on-surface"
        @click="stopWriting"
      >
        <MsIcon name="progress_activity" :size="20" class="animate-spin" />
        Ждём метку — отменить
      </button>
    </section>

    <NfcTagSheet
      v-if="tag"
      :tag="tag"
      @write="tag = null"
      @close="tag = null"
    />
  </div>
</template>
