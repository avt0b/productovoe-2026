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

const missing = computed(() => (name.value.trim() ? null : 'Как называется отряд?'))

async function submit(): Promise<void> {
  if (missing.value || saving.value) return
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
      <FormInput v-model="region" label="Где работает" :maxlength="120" placeholder="Орёл" hint="Город штаба — по нему отряд встанет на карту потребностей" />
      <FormTextarea v-model="description" label="Чем занимается" placeholder="Какие рубежи, какие экспедиции" />
      <FormInput v-model="contact" label="Как связаться" :maxlength="300" placeholder="Телефон штаба или ссылка на чат" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'flag'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>Создать отряд</span>
      </button>
    </form>
  </SheetDialog>
</template>
