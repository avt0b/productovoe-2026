<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'

import { appPath, tagPayload, type NfcTag } from './nfc'

/** Что оказалось на метке: ссылка в приложение, обычная ссылка или текст. */
const props = defineProps<{ tag: NfcTag }>()

const emit = defineEmits<{ close: []; write: [] }>()

const router = useRouter()

const payload = computed(() => tagPayload(props.tag))
const inApp = computed(() => appPath(payload.value?.uri))
/** Экран, на который ведёт метка, может быть отключён вместе со своим модулем. */
const knownScreen = computed(() => {
  const path = inApp.value
  return path !== null && router.resolve(path).matched.length > 0
})
const webLink = computed(() => (payload.value?.uri?.startsWith('http') ? payload.value.uri : null))

const details = computed(() => [
  { label: 'Номер метки', value: props.tag.id ?? '—' },
  { label: 'Тип', value: props.tag.techs.join(', ') || '—' },
  {
    label: 'Память',
    value: props.tag.maxSize === null ? 'не сообщает' : `${props.tag.maxSize} байт`,
  },
  { label: 'Запись', value: props.tag.writable ? 'разрешена' : 'закрыта' },
])

function open(): void {
  const path = inApp.value
  if (!path) return
  emit('close')
  void router.push(path)
}
</script>

<template>
  <SheetDialog title="Метка прочитана" :subtitle="tag.error ?? undefined" @close="emit('close')">
    <div class="flex flex-col gap-space-md">
      <div class="flex items-start gap-space-sm rounded-2xl bg-surface-container-low p-space-md">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container" aria-hidden="true">
          <MsIcon name="nfc" :size="18" />
        </span>
        <div class="min-w-0 flex-1">
          <span class="block font-archival text-archival uppercase text-on-surface-variant">
            {{ payload?.kind === 'uri' ? 'Ссылка' : payload?.kind === 'text' ? 'Текст' : 'Содержимое' }}
          </span>
          <p v-if="payload?.text" class="whitespace-pre-line font-body-md text-body-md text-on-surface">{{ payload.text }}</p>
          <p v-else-if="payload?.uri" class="break-all font-body-md text-body-md text-on-surface">{{ payload.uri }}</p>
          <p v-else class="font-body-md text-body-md text-on-surface-variant">Метка пустая — на неё можно записать ссылку или текст.</p>
        </div>
      </div>

      <button
        v-if="inApp && knownScreen"
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="open"
      >
        <MsIcon name="open_in_new" :size="18" />
        <span>Открыть в приложении</span>
      </button>
      <p v-else-if="inApp" class="rounded-2xl bg-surface-container-low px-space-sm py-2 font-body-sm text-body-sm text-on-surface-variant">
        Метка ведёт на экран «{{ inApp }}», которого в этой сборке нет.
      </p>
      <a
        v-else-if="webLink"
        :href="webLink"
        target="_blank"
        rel="noopener"
        class="flex items-center justify-center gap-space-xs rounded-full bg-secondary py-3 font-label-lg text-label-lg text-on-secondary active:scale-[0.99]"
      >
        <MsIcon name="open_in_new" :size="18" />
        Открыть ссылку
      </a>

      <dl class="flex flex-col divide-y divide-outline-variant/60 rounded-2xl bg-surface-container-lowest px-space-md shadow-document">
        <div v-for="row in details" :key="row.label" class="flex items-baseline justify-between gap-space-sm py-2">
          <dt class="shrink-0 font-label-md text-label-md text-on-surface-variant">{{ row.label }}</dt>
          <dd class="min-w-0 truncate font-label-md text-label-md text-on-surface">{{ row.value }}</dd>
        </div>
      </dl>

      <button
        v-if="tag.writable"
        type="button"
        class="flex items-center justify-center gap-space-xs self-center rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="emit('write')"
      >
        <MsIcon name="edit" :size="18" />
        Записать на метку
      </button>
    </div>
  </SheetDialog>
</template>
