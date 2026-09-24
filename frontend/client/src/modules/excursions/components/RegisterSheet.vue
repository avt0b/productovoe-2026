<script setup lang="ts">
import { computed, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'

import type { RegistrationDraft } from '../data'

/**
 * Запись на экскурсию: сам или всей школой.
 *
 * Коллективная заявка из ТЗ — это одна регистрация на всю группу, а не
 * двадцать отдельных: краеведу важно знать, что придёт 7«А» из школы №19 и
 * сколько их, а не двадцать одинаковых строк без имени.
 */
const props = defineProps<{
  /** Сколько мест осталось: больше этого группу не записать. */
  seatsLeft: number
  busy: boolean
}>()

const emit = defineEmits<{ close: []; submit: [draft: RegistrationDraft | undefined] }>()

type Kind = 'self' | 'group'

const kind = ref<Kind>('self')
const organization = ref('')
const size = ref<number | null>(10)

const groupSize = computed(() => Math.max(1, Math.round(size.value ?? 1)))

const problem = computed(() => {
  if (kind.value === 'self') return null
  if (!organization.value.trim()) return 'Напишите, от кого заявка: школа, класс, клуб.'
  if (groupSize.value > props.seatsLeft) return `Мест осталось ${props.seatsLeft} — группа не поместится.`
  return null
})

function submit(): void {
  if (props.busy || problem.value) return
  emit(
    'submit',
    kind.value === 'self'
      ? undefined
      : { organization_name: organization.value.trim(), group_size: groupSize.value },
  )
}
</script>

<template>
  <SheetDialog title="Запись на экскурсию" :subtitle="`Свободных мест: ${seatsLeft}`" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <!-- Выбор вида заявки: подложка переезжает, как переключатель на экране входа -->
      <div class="relative grid grid-cols-2 rounded-xl border border-outline-variant bg-surface-container-low p-1 text-center" role="tablist">
        <span
          class="absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-lg bg-surface-container-lowest shadow-float transition-transform duration-300 ease-out"
          :class="kind === 'group' ? 'translate-x-full' : 'translate-x-0'"
          aria-hidden="true"
        />
        <button
          v-for="tab in [
            { value: 'self', title: 'Иду сам' },
            { value: 'group', title: 'От школы или клуба' },
          ] as const"
          :key="tab.value"
          type="button"
          role="tab"
          :aria-selected="kind === tab.value"
          class="relative z-10 rounded-lg px-2 py-2 font-label-md text-label-md transition-colors duration-200"
          :class="kind === tab.value ? 'text-on-surface' : 'text-on-surface-variant'"
          @click="kind = tab.value"
        >
          {{ tab.title }}
        </button>
      </div>

      <!--
        Поля организации не снимаются с разметки, а схлопываются: иначе окно
        прыгало бы на полэкрана при каждом переключении вида заявки.
      -->
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="kind === 'group' ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="kind !== 'group'"
      >
        <div class="overflow-hidden">
          <div class="flex flex-col gap-space-md pb-1">
            <FormInput
              v-model="organization"
              label="От кого заявка"
              icon="school"
              placeholder="Школа № 19, 7 «А» класс"
              :maxlength="255"
            />
            <FormInput
              v-model="size"
              label="Сколько человек"
              icon="groups"
              type="number"
              :min="1"
              :max="300"
              inputmode="numeric"
              hint="Вместе с сопровождающими"
            />
          </div>
        </div>
      </div>

      <p v-if="problem" class="font-body-sm text-body-sm text-error" role="alert">{{ problem }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-60"
        :disabled="busy || problem !== null"
      >
        <MsIcon :name="busy ? 'progress_activity' : 'how_to_reg'" :size="20" :class="{ 'animate-spin': busy }" />
        {{ kind === 'self' ? 'Записаться' : `Записать группу · ${groupSize}` }}
      </button>
    </form>
  </SheetDialog>
</template>
