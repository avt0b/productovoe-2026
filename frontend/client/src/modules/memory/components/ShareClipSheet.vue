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
 * само письмо или сообщение пока не уходит — окно так и говорит.
 */
const props = defineProps<{ clip: Clip }>()

const emit = defineEmits<{ close: [] }>()

const recipient = ref('')
const note = ref('')
const saving = ref(false)
const error = ref<string | null>(null)
const done = ref(false)

const valid = computed(() => recipient.value.trim().length > 0)

async function submit(): Promise<void> {
  if (!valid.value || saving.value) return
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
</script>

<template>
  <SheetDialog title="Отправить родным" :subtitle="clip.soldier_name || undefined" @close="emit('close')">
    <div v-if="done" class="flex flex-col items-center gap-space-md py-space-md text-center">
      <MsIcon name="mark_email_read" :size="40" class="text-secondary" />
      <p class="font-body-md text-body-md text-on-surface">
        Записали: {{ recipient }}. Письма и сообщения из приложения пока не отправляются — передайте ссылку сами.
      </p>
      <button type="button" class="w-full rounded-full bg-secondary py-3 font-label-lg text-label-lg text-on-secondary" @click="emit('close')">
        Готово
      </button>
    </div>
    <form v-else class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormInput v-model="recipient" label="Кому" :maxlength="300" placeholder="Почта, телефон или имя родственника" required />
      <FormTextarea v-model="note" label="Пара слов" :rows="2" :maxlength="1000" placeholder="Нашли прадеда — посмотри" />
      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary disabled:opacity-60"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'send'" :size="20" :class="{ 'animate-spin': saving }" />
        Отправить
      </button>
    </form>
  </SheetDialog>
</template>
