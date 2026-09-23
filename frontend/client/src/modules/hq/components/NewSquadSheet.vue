<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { createSquad, type Squad } from '../data'

const emit = defineEmits<{ close: []; created: [squad: Squad] }>()

const name = ref('')
const region = ref('')
const description = ref('')
const contact = ref('')
const saving = ref(false)
const error = ref<string | null>(null)

const valid = computed(() => name.value.trim().length > 0)

async function submit(): Promise<void> {
  if (!valid.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    const squad = await createSquad({
      name: name.value.trim(),
      region: region.value.trim(),
      description: description.value.trim(),
      contact: contact.value.trim(),
    })
    emit('created', squad)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Новый поисковый отряд" subtitle="Вы станете его командиром" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormInput v-model="name" label="Название" :maxlength="200" placeholder="Поисковый отряд «Высота»" required />
      <FormInput v-model="region" label="Где работает" :maxlength="120" placeholder="Орёл" />
      <FormTextarea v-model="description" label="Чем занимается" placeholder="Какие рубежи, какие экспедиции" />
      <FormInput v-model="contact" label="Как связаться" :maxlength="300" placeholder="Телефон штаба или ссылка на чат" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'flag'" :size="20" :class="{ 'animate-spin': saving }" />
        Создать отряд
      </button>
    </form>
  </SheetDialog>
</template>
