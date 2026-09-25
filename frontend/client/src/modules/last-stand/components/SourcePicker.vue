<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'

import { MEMORY_BOOK_VOLUMES, SOURCE_KINDS, formatSource, type SourceDraft, type SourceKind } from '../data'

/**
 * Откуда известно о месте: вид источника и его реквизиты. Снизу — фраза
 * целиком, как её увидит краевед: по ней сразу видно, найдётся ли документ.
 */
const draft = defineModel<SourceDraft>({ required: true })

// Выпадающий список общего кита работает со строками — том храним числом.
const volumeOptions = Array.from({ length: MEMORY_BOOK_VOLUMES }, (_, index) => ({
  value: String(index + 1),
  title: `Том ${index + 1}`,
}))

const preview = computed(() => formatSource(draft.value))

function pick(kind: SourceKind): void {
  draft.value = { ...draft.value, kind }
}

/**
 * Поля каждого вида не снимаются с разметки, а схлопываются: при смене вида
 * форма иначе прыгала бы на высоту целого поля под пальцем.
 */
function openWhen(...kinds: SourceKind[]): { open: boolean; inert: boolean } {
  const open = kinds.includes(draft.value.kind)
  return { open, inert: !open }
}

function patch(field: keyof SourceDraft, value: unknown): void {
  draft.value = { ...draft.value, [field]: value }
}
</script>

<template>
  <div class="flex flex-col gap-space-sm">
    <div class="grid grid-cols-2 gap-space-xs" role="radiogroup" aria-label="Вид источника">
      <button
        v-for="kind in SOURCE_KINDS"
        :key="kind.value"
        type="button"
        role="radio"
        :aria-checked="draft.kind === kind.value"
        class="flex items-center gap-space-xs rounded-lg px-space-sm py-2 text-left font-label-md text-label-md transition-colors duration-200 active:scale-95"
        :class="
          draft.kind === kind.value
            ? 'bg-tertiary-fixed text-on-tertiary-fixed shadow-document'
            : 'bg-surface-container-low text-on-surface-variant'
        "
        @click="pick(kind.value)"
      >
        <MsIcon :name="kind.icon" :size="18" :filled="draft.kind === kind.value" class="shrink-0" />
        <span class="min-w-0 truncate">{{ kind.title }}</span>
      </button>
    </div>

    <!-- Книга Памяти: том и страница -->
    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="openWhen('memory_book').open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="openWhen('memory_book').inert"
    >
      <div class="overflow-hidden">
        <div class="grid grid-cols-2 gap-space-sm">
          <FormSelect
            :model-value="draft.volume ? String(draft.volume) : ''"
            label="Том"
            :options="volumeOptions"
            placeholder="Выберите"
            @update:model-value="(value) => patch('volume', value ? Number(value) : null)"
          />
          <FormInput
            :model-value="draft.page"
            label="Страница"
            type="number"
            inputmode="numeric"
            :min="1"
            @update:model-value="(value) => patch('page', value)"
          />
        </div>
      </div>
    </div>

    <!-- Сборник: только страница -->
    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="openWhen('collection').open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="openWhen('collection').inert"
    >
      <div class="overflow-hidden">
        <FormInput
          :model-value="draft.page"
          label="Страница сборника"
          type="number"
          inputmode="numeric"
          :min="1"
          @update:model-value="(value) => patch('page', value)"
        />
      </div>
    </div>

    <!-- «Память народа»: номер донесения или ссылка -->
    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="openWhen('people_memory').open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="openWhen('people_memory').inert"
    >
      <div class="overflow-hidden">
        <FormInput
          :model-value="draft.reference"
          label="Донесение или ссылка"
          :maxlength="200"
          placeholder="Донесение о потерях № 1234 или pamyat-naroda.ru/…"
          @update:model-value="(value) => patch('reference', value)"
        />
      </div>
    </div>

    <!-- Рассказ жителя и отчёт экспедиции: кто -->
    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="openWhen('witness', 'expedition').open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="openWhen('witness', 'expedition').inert"
    >
      <div class="overflow-hidden">
        <FormInput
          :model-value="draft.who"
          :label="draft.kind === 'expedition' ? 'Отряд и год' : 'Кто рассказал'"
          :maxlength="160"
          :placeholder="draft.kind === 'expedition' ? '«Высота», Вахта Памяти-2024' : 'Мария Ивановна, д. Крупышино'"
          @update:model-value="(value) => patch('who', value)"
        />
      </div>
    </div>

    <FormInput
      :model-value="draft.note"
      :label="draft.kind === 'other' ? 'Что за источник' : 'Уточнение'"
      :maxlength="200"
      :placeholder="draft.kind === 'other' ? 'Музей, фонд, опись' : 'Необязательно'"
      @update:model-value="(value) => patch('note', value)"
    />

    <p
      class="flex items-start gap-space-xs rounded-lg px-space-sm py-2 font-body-sm text-body-sm"
      :class="preview ? 'bg-surface-container-low text-on-surface' : 'bg-surface-container-low text-on-surface-variant'"
      role="status"
    >
      <MsIcon name="format_quote" :size="18" class="mt-0.5 shrink-0 text-tertiary" />
      <span>{{ preview || 'Без источника администратор не сможет подтвердить место архивом — укажите, откуда сведения.' }}</span>
    </p>
  </div>
</template>
