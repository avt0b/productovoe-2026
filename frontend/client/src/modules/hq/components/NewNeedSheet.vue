<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { NEED_KINDS, createNeed, type Need, type NeedKind, type Squad } from '../data'

/** Потребность отряда: целевой сбор («Поднять бойца», «Экипировать отряд»), люди или снаряжение. */
const props = defineProps<{ squads: Squad[] }>()

const emit = defineEmits<{ close: []; created: [need: Need] }>()

const squadId = ref<string>(props.squads[0]?.id ?? '')
const kind = ref<NeedKind | ''>('funds')
const title = ref('')
const description = ref('')
const target = ref<number | null>(50_000)
const saving = ref(false)
const error = ref<string | null>(null)

const squadOptions = computed(() => props.squads.map((squad) => ({ value: squad.id, title: squad.name })))
const kindOptions = (Object.keys(NEED_KINDS) as NeedKind[]).map((value) => ({ value, title: NEED_KINDS[value].title }))
const isFunds = computed(() => kind.value === 'funds')
const valid = computed(
  () =>
    squadId.value !== '' &&
    kind.value !== '' &&
    title.value.trim().length > 0 &&
    (!isFunds.value || (target.value !== null && target.value >= 1)),
)

async function submit(): Promise<void> {
  if (!valid.value || saving.value || kind.value === '') return
  saving.value = true
  error.value = null
  try {
    const need = await createNeed(squadId.value, {
      kind: kind.value,
      title: title.value.trim(),
      description: description.value.trim(),
      target_amount: isFunds.value ? Math.round(target.value ?? 1) : null,
    })
    emit('created', need)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Что нужно отряду" subtitle="Появится на карте потребностей штаба" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormSelect v-if="squads.length > 1" v-model="squadId" label="Отряд" :options="squadOptions" />
      <FormSelect v-model="kind" label="Что нужно" :options="kindOptions" />
      <FormInput
        v-model="title"
        label="Коротко"
        :maxlength="255"
        :placeholder="isFunds ? 'Поднять бойца: ГСМ и генератор' : 'Нужны люди на раскопки'"
        required
      />
      <FormTextarea v-model="description" label="Подробнее" :rows="3" />
      <FormInput v-if="isFunds" v-model="target" label="Цель сбора, ₽" type="number" inputmode="numeric" :min="1" :step="1" required />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'add_circle'" :size="20" :class="{ 'animate-spin': saving }" />
        Опубликовать
      </button>
    </form>
  </SheetDialog>
</template>
