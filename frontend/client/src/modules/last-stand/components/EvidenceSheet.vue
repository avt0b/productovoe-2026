<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { addEvidence, type FindRecord } from '../data'

/**
 * «Дополнить данными»: сведения о месте уходят в народный архив с его
 * координатами — краевед проверит их по Книге Памяти, как любую запись.
 */
const props = defineProps<{ record: FindRecord }>()

const emit = defineEmits<{ close: [] }>()

const title = ref(`Сведения о месте: ${props.record.title}`)
const body = ref('')
const mediaUrl = ref('')
const saving = ref(false)
const error = ref<string | null>(null)
const done = ref(false)

const mediaValid = computed(() => !mediaUrl.value.trim() || /^https?:\/\/\S+$/i.test(mediaUrl.value.trim()))
const valid = computed(() => title.value.trim().length > 0 && body.value.trim().length > 0 && mediaValid.value)

async function submit(): Promise<void> {
  if (!valid.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    await addEvidence(props.record, title.value.trim(), body.value.trim(), mediaUrl.value.trim())
    done.value = true
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Дополнить данными" :subtitle="record.coordinates" @close="emit('close')">
    <div v-if="done" class="flex flex-col items-center gap-space-md py-space-md text-center">
      <span class="flex h-14 w-14 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
        <MsIcon name="task_alt" :size="28" filled />
      </span>
      <p class="font-body-md text-body-md text-on-surface">
        Спасибо! Сведения ушли краеведу: после проверки они появятся в народном архиве рядом с этим местом.
      </p>
      <button
        type="button"
        class="flex w-full items-center justify-center rounded-full bg-surface-container-high px-space-md py-2.5 font-label-lg text-label-lg text-on-surface active:scale-95"
        @click="emit('close')"
      >
        Готово
      </button>
    </div>
    <form v-else class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormInput v-model="title" label="Заголовок" :maxlength="255" required />
      <FormTextarea
        v-model="body"
        label="Что известно"
        :rows="4"
        placeholder="Номер донесения о потерях, рассказ жителей, выписка из Книги Памяти"
        required
      />
      <FormInput v-model="mediaUrl" label="Ссылка на документ или фото" type="url" inputmode="url" :maxlength="500" placeholder="https://…" />
      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <InlineNotice v-else-if="!mediaValid" tone="error">Нужна ссылка вида https://…</InlineNotice>
      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'send'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>Отправить краеведу</span>
      </button>
    </form>
  </SheetDialog>
</template>
