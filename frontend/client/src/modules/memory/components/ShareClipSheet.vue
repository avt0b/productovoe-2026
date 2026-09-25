<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { shareClip, type Clip } from '../data'

/**
 * «Отправить родным» из кейса. Сервис записывает, кому и что отправлено;
 * само письмо или сообщение пока не уходит — окно так и говорит и даёт
 * отправить ссылку самому, через системное окно или буфер обмена.
 */
const props = defineProps<{ clip: Clip }>()

const emit = defineEmits<{ close: [] }>()

const recipient = ref('')
const note = ref('')
const saving = ref(false)
const error = ref<string | null>(null)
const done = ref(false)
const copied = ref(false)

const missing = computed(() => (recipient.value.trim() ? null : 'Кому отправить — почта, телефон или имя'))

async function submit(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    await shareClip(props.clip.id, recipient.value.trim(), note.value.trim())
    done.value = true
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

/** Системное окно «Поделиться», а где его нет (WebView Android) — буфер обмена. */
async function passLink(): Promise<void> {
  const url = props.clip.video_url
  if (!url) return
  const text = [note.value.trim(), `${props.clip.soldier_name || 'Живое фото'} — «Маршруты победы»`].filter(Boolean).join('\n')
  try {
    if (navigator.share) {
      await navigator.share({ title: props.clip.soldier_name || 'Живое фото', text, url })
      return
    }
    await navigator.clipboard.writeText(`${text}\n${url}`)
    copied.value = true
  } catch {
    /* человек закрыл окно «Поделиться» */
  }
}
</script>

<template>
  <SheetDialog title="Отправить родным" :subtitle="clip.soldier_name || undefined" @close="emit('close')">
    <div v-if="done" class="flex flex-col items-center gap-space-md py-space-md text-center" role="status">
      <span class="flex h-14 w-14 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
        <MsIcon name="mark_email_read" :size="28" />
      </span>
      <p class="font-body-md text-body-md text-on-surface">
        Записали: {{ recipient }}. Письма и сообщения из приложения пока не уходят — передайте ссылку сами.
      </p>
      <button
        v-if="clip.video_url"
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="passLink"
      >
        <MsIcon :name="copied ? 'check' : 'share'" :size="18" />
        <span>{{ copied ? 'Ссылка скопирована' : 'Передать ссылку' }}</span>
      </button>
      <button
        type="button"
        class="rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="emit('close')"
      >
        Готово
      </button>
    </div>
    <form v-else class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormInput v-model="recipient" label="Кому" :maxlength="300" placeholder="Почта, телефон или имя родственника" required />
      <FormTextarea v-model="note" label="Пара слов" :rows="2" :maxlength="1000" placeholder="Нашли прадеда — посмотри" />
      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>
      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'send'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>Отправить</span>
      </button>
    </form>
  </SheetDialog>
</template>
