<script setup lang="ts">
import { computed, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import ConfirmAction from '@/ui/ConfirmAction.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import {
  CAMPAIGN_KINDS,
  NEED_KINDS,
  campaignTitle,
  createNeed,
  deleteNeed,
  updateNeed,
  type CampaignKind,
  type Need,
  type NeedKind,
  type Squad,
} from '../data'

/**
 * Потребность отряда: целевой сбор («Поднять бойца», «Экипировать отряд»),
 * люди или снаряжение.
 *
 * Это же окно правит уже опубликованную потребность. Вид и отряд при правке не
 * меняются — сервис их не принимает, — а заголовок правится как есть, без
 * повторной приставки вида сбора. Ошибочную потребность можно удалить; сбор,
 * в который уже пришли деньги, — только закрыть.
 */
const props = withDefaults(defineProps<{ squads: Squad[]; need?: Need | null }>(), { need: null })

const emit = defineEmits<{ close: []; created: [need: Need]; done: [text: string] }>()

/** Лимит сервиса на заголовок. */
const TITLE_MAX = 255

const squadId = ref<string>(props.need?.squad_id ?? props.squads[0]?.id ?? '')
const kind = ref<NeedKind>(props.need?.kind ?? 'funds')
const campaign = ref<CampaignKind>('raise')
const title = ref(props.need?.title ?? '')
const description = ref(props.need?.description ?? '')
const target = ref<number | null>(props.need?.target_amount ?? 50_000)
const saving = ref(false)
const error = ref<string | null>(null)

const squadOptions = computed(() => props.squads.map((squad) => ({ value: squad.id, title: squad.name })))
const kinds = Object.keys(NEED_KINDS) as NeedKind[]
const campaigns = Object.keys(CAMPAIGN_KINDS) as CampaignKind[]
const isFunds = computed(() => kind.value === 'funds')

/** Вид сбора уходит в начало заголовка — на него и ужимаем лимит поля. */
const titleMax = computed(() => (isFunds.value && campaign.value !== 'other' ? TITLE_MAX - CAMPAIGN_KINDS[campaign.value].title.length - 2 : TITLE_MAX))
const placeholder = computed(() => {
  if (kind.value === 'volunteers') return 'Нужны люди на раскопки'
  if (kind.value === 'equipment') return 'Нужны щупы и палатки'
  return campaign.value === 'equip' ? 'Металлоискатели и щупы' : campaign.value === 'raise' ? 'ГСМ и генератор' : 'На что собираем'
})

const missing = computed(() => {
  if (!squadId.value) return 'Выберите отряд'
  if (!title.value.trim()) return 'Коротко напишите, что нужно'
  if (isFunds.value && (target.value === null || target.value < 1)) return 'Укажите цель сбора в рублях'
  return null
})

async function submit(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    if (props.need) {
      emit(
        'created',
        await updateNeed(props.need.id, {
          title: title.value.trim(),
          description: description.value.trim(),
          target_amount: isFunds.value ? Math.round(target.value ?? 1) : null,
        }),
      )
    } else {
      emit(
        'created',
        await createNeed(squadId.value, {
          kind: kind.value,
          title: isFunds.value ? campaignTitle(campaign.value, title.value.trim()) : title.value.trim(),
          description: description.value.trim(),
          target_amount: isFunds.value ? Math.round(target.value ?? 1) : null,
        }),
      )
    }
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

async function remove(): Promise<void> {
  const need = props.need
  if (!need || saving.value) return
  saving.value = true
  error.value = null
  try {
    await deleteNeed(need.id)
    emit('done', `«${need.title}» удалено`)
  } catch (reason) {
    // Взносы уже пришли — деньги не исчезают вместе со сбором, его закрывают.
    error.value =
      reason instanceof ApiError && reason.status === 409
        ? 'В сбор уже пришли взносы — удалить его нельзя. Закройте сбор кнопкой на его карточке.'
        : errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog
    :title="need ? 'Изменить потребность' : 'Что нужно отряду'"
    :subtitle="need ? 'Волонтёры увидят новые сведения' : 'Появится в штабе и на карте потребностей'"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormSelect v-if="!need && squads.length > 1" v-model="squadId" label="Отряд" :options="squadOptions" />

      <div v-if="!need" class="grid grid-cols-3 gap-space-xs" role="radiogroup" aria-label="Что нужно">
        <button
          v-for="value in kinds"
          :key="value"
          type="button"
          role="radio"
          :aria-checked="kind === value"
          class="flex flex-col items-center gap-1 rounded-2xl px-1 py-space-sm text-center font-label-md text-label-md transition-colors duration-200 active:scale-95"
          :class="kind === value ? 'bg-secondary-container text-on-secondary-container shadow-document' : 'bg-surface-container-low text-on-surface-variant'"
          @click="kind = value"
        >
          <MsIcon :name="NEED_KINDS[value].icon" :size="20" :filled="kind === value" />
          {{ NEED_KINDS[value].title }}
        </button>
      </div>

      <!-- Вид сбора — только у денег и только при создании: в заголовке он уже есть. -->
      <div
        class="-mt-space-md grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="isFunds && !need ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!isFunds || need !== null"
      >
        <div class="overflow-hidden">
          <div class="flex flex-col gap-space-xs pt-space-md">
            <span class="font-archival text-archival uppercase text-on-surface-variant">Вид сбора</span>
            <div class="flex flex-wrap gap-space-xs" role="radiogroup" aria-label="Вид сбора">
              <button
                v-for="value in campaigns"
                :key="value"
                type="button"
                role="radio"
                :aria-checked="campaign === value"
                class="flex items-center gap-1 rounded-full px-space-sm py-1.5 font-label-md text-label-md transition-colors duration-200 active:scale-95"
                :class="campaign === value ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-on-surface'"
                @click="campaign = value"
              >
                <MsIcon :name="CAMPAIGN_KINDS[value].icon" :size="15" />
                {{ CAMPAIGN_KINDS[value].title }}
              </button>
            </div>
            <p class="font-body-sm text-body-sm text-on-surface-variant">{{ CAMPAIGN_KINDS[campaign].hint }}</p>
          </div>
        </div>
      </div>

      <FormInput v-model="title" label="Коротко" :maxlength="titleMax" :placeholder="placeholder" required />
      <FormTextarea v-model="description" label="Подробнее" :rows="3" placeholder="Когда, куда, сколько людей" />

      <div
        class="-mt-space-md grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="isFunds ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!isFunds"
      >
        <div class="overflow-hidden">
          <div class="pt-space-md">
            <FormInput v-model="target" label="Цель сбора, ₽" type="number" inputmode="numeric" :min="1" :step="1" />
          </div>
        </div>
      </div>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'add_circle'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ need ? 'Сохранить' : 'Опубликовать' }}</span>
      </button>

      <ConfirmAction
        v-if="need"
        class="border-t border-outline-variant/40 pt-space-sm"
        :label="need.kind === 'funds' ? 'Удалить сбор' : 'Удалить потребность'"
        icon="delete"
        :warning="
          need.kind === 'funds'
            ? 'Сбор исчезнет из штаба и с карты. Если взносы уже пришли, удалить не выйдет — такой сбор закрывают.'
            : 'Потребность исчезнет из штаба и с карты потребностей.'
        "
        confirm-label="Удалить"
        :busy="saving"
        @confirm="remove"
      />
    </form>
  </SheetDialog>
</template>
