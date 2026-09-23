<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'

import { uploadPhoto, type UploadService } from '../data'

/**
 * Фото для заявки: снимок с телефона или ссылка из «Памяти народа», музея,
 * семейного альбома в облаке. Снимок загружается сразу после выбора — к
 * отправке формы адрес уже готов, и человек видит, что фото принято.
 */
const props = defineProps<{
  service: UploadService
  label: string
  hint?: string
}>()

/** Адрес фото — то, что уходит в заявку. Пустая строка — фото нет. */
const url = defineModel<string>({ required: true })
/** Идёт загрузка — форма не отправляется, пока адреса нет. */
const uploading = defineModel<boolean>('uploading', { default: false })

type Mode = 'device' | 'link'
const mode = ref<Mode>('device')
const input = ref<HTMLInputElement | null>(null)
const localPreview = ref<string | null>(null)
const error = ref<string | null>(null)
const link = ref('')

/** Лимиты сервисов: `media_service` — 15 МБ, `archive_service` — 20 МБ. */
const maxMegabytes = computed(() => (props.service === 'media' ? 15 : 20))
const linkValid = computed(() => /^https?:\/\/\S+$/i.test(link.value.trim()))
const preview = computed(() => (mode.value === 'device' ? (localPreview.value ?? (url.value || null)) : linkValid.value ? link.value.trim() : null))

function setMode(next: Mode): void {
  mode.value = next
  error.value = null
  url.value = next === 'link' ? (linkValid.value ? link.value.trim() : '') : ''
  if (next === 'link') dropPreview()
}

function onLink(value: string | number | null): void {
  link.value = String(value ?? '')
  url.value = linkValid.value ? link.value.trim() : ''
}

function dropPreview(): void {
  if (localPreview.value) URL.revokeObjectURL(localPreview.value)
  localPreview.value = null
}

async function onFile(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  ;(event.target as HTMLInputElement).value = ''
  if (!file) return
  dropPreview()
  localPreview.value = URL.createObjectURL(file)
  url.value = ''
  error.value = null
  uploading.value = true
  try {
    url.value = await uploadPhoto(props.service, file)
  } catch (reason) {
    dropPreview()
    // 503 — хранилище фото не поднято (так бывает на стенде); ссылка при этом работает.
    error.value =
      reason instanceof ApiError && reason.status === 503
        ? 'Хранилище фото сейчас недоступно. Вставьте ссылку на снимок — так заявка тоже примется.'
        : errorText(reason)
  } finally {
    uploading.value = false
  }
}

onBeforeUnmount(dropPreview)
</script>

<template>
  <div class="flex flex-col gap-space-sm">
    <div class="flex items-center justify-between gap-space-sm">
      <span class="font-label-md text-label-md text-on-surface">{{ label }}</span>
      <div class="relative grid grid-cols-2 rounded-xl bg-surface-container p-1" role="tablist" :aria-label="label">
        <span
          class="absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-lg bg-surface-container-lowest shadow-float transition-transform duration-300 ease-out"
          :class="mode === 'link' ? 'translate-x-full' : 'translate-x-0'"
          aria-hidden="true"
        />
        <button
          v-for="option in [
            { value: 'device', title: 'С телефона' },
            { value: 'link', title: 'По ссылке' },
          ] as const"
          :key="option.value"
          type="button"
          role="tab"
          :aria-selected="mode === option.value"
          class="relative z-10 whitespace-nowrap rounded-lg px-space-sm py-1 font-label-sm text-label-sm transition-colors duration-200"
          :class="mode === option.value ? 'text-on-surface' : 'text-on-surface-variant'"
          @click="setMode(option.value)"
        >
          {{ option.title }}
        </button>
      </div>
    </div>

    <input ref="input" type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" tabindex="-1" @change="onFile" />

    <button
      v-if="mode === 'device'"
      type="button"
      class="relative flex min-h-36 items-center justify-center overflow-hidden rounded-2xl border border-dashed border-outline-variant bg-surface-container-low text-on-surface-variant transition-colors duration-200 hover:bg-surface-container active:scale-[0.99]"
      :aria-busy="uploading"
      @click="input?.click()"
    >
      <template v-if="preview">
        <img :src="preview" alt="Выбранное фото" class="h-44 w-full object-contain" />
        <span
          class="absolute bottom-space-sm right-space-sm flex items-center gap-1 rounded-full border border-white/15 bg-night/45 px-space-sm py-1 font-label-sm text-label-sm text-white backdrop-blur-md"
        >
          <MsIcon :name="uploading ? 'progress_activity' : 'check'" :size="15" :class="{ 'animate-spin': uploading }" />
          {{ uploading ? 'Загружаем…' : 'Заменить' }}
        </span>
      </template>
      <span v-else class="flex flex-col items-center gap-space-xs px-space-md py-space-md text-center">
        <MsIcon name="add_a_photo" :size="28" />
        <span class="font-label-md text-label-md text-on-surface">Выбрать снимок</span>
        <span class="font-body-sm text-body-sm">JPEG, PNG или WebP, до {{ maxMegabytes }} МБ</span>
      </span>
    </button>

    <template v-else>
      <FormInput
        :model-value="link"
        label="Ссылка на фото"
        type="url"
        inputmode="url"
        :maxlength="500"
        placeholder="https://…"
        @update:model-value="onLink"
      />
      <img v-if="preview" :src="preview" alt="Фото по ссылке" class="h-40 w-32 self-center rounded-2xl object-cover shadow-document" />
      <p v-else-if="link.trim()" class="font-body-sm text-body-sm text-error" role="alert">Нужна ссылка вида https://…</p>
    </template>

    <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
    <p v-else-if="hint" class="font-body-sm text-body-sm text-on-surface-variant">{{ hint }}</p>
  </div>
</template>
