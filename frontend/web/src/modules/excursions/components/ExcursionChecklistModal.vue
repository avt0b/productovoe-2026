<script setup>
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  excursion: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue'])

// Чисто фронтовый чек-лист «что взять с собой» — ни в одном сервисе нет
// сущности для персональных сборов на экскурсию, поэтому храним отметки в
// localStorage, отдельно на каждую экскурсию (по её id).
const ITEMS = [
  { id: 'gloves', icon: 'back_hand', label: 'Перчатки' },
  { id: 'shovel', icon: 'construction', label: 'Сапёрная лопата' },
  { id: 'bags', icon: 'shopping_bag', label: 'Пакеты и мешки для находок' },
  { id: 'water', icon: 'water_drop', label: 'Питьевая вода' },
  { id: 'food', icon: 'lunch_dining', label: 'Еда, перекус' },
  { id: 'first_aid', icon: 'medical_services', label: 'Аптечка' },
  { id: 'flashlight', icon: 'flashlight_on', label: 'Фонарик' },
  { id: 'raincoat', icon: 'rainy', label: 'Дождевик' },
  { id: 'warm_clothes', icon: 'checkroom', label: 'Тёплая одежда по погоде' },
  { id: 'documents', icon: 'badge', label: 'Документ, удостоверяющий личность' },
]

function storageKey(excursionId) {
  return `marshruty.excursion-checklist.${excursionId}`
}

const checked = reactive({})

function load(excursionId) {
  Object.keys(checked).forEach((k) => delete checked[k])
  if (!excursionId) return
  try {
    const raw = localStorage.getItem(storageKey(excursionId))
    Object.assign(checked, raw ? JSON.parse(raw) : {})
  } catch {
    // приватный режим браузера — просто без сохранения
  }
}

function persist() {
  if (!props.excursion) return
  try {
    localStorage.setItem(storageKey(props.excursion.id), JSON.stringify(checked))
  } catch {
    // переполненное хранилище/приватный режим — не критично для демо-чек-листа
  }
}

watch(
  () => [props.modelValue, props.excursion?.id],
  ([open, excursionId]) => {
    if (open) load(excursionId)
  },
)

function toggle(itemId) {
  checked[itemId] = !checked[itemId]
  persist()
}

const doneCount = computed(() => ITEMS.filter((item) => checked[item.id]).length)

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <div
    v-if="modelValue && excursion"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-md w-full shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
      <div class="flex items-center justify-between p-5 border-b border-surface-container-high shrink-0">
        <div class="flex flex-col min-w-0">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold">Что взять с собой</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant truncate">{{ excursion.title }}</span>
        </div>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors shrink-0"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <div class="p-5 flex flex-col gap-2 overflow-y-auto">
        <div class="flex items-center justify-between pb-1">
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Чек-лист сборов</span>
          <span class="font-label-sm text-label-sm text-secondary font-bold">{{ doneCount }} из {{ ITEMS.length }}</span>
        </div>
        <label
          v-for="item in ITEMS"
          :key="item.id"
          class="flex items-center gap-3 p-3 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container cursor-pointer transition-colors select-none"
        >
          <input
            type="checkbox"
            class="w-5 h-5 rounded accent-primary cursor-pointer"
            :checked="!!checked[item.id]"
            @change="toggle(item.id)"
          />
          <span class="material-symbols-outlined text-on-surface-variant text-[20px]">{{ item.icon }}</span>
          <span
            class="font-body-md text-body-md flex-1"
            :class="checked[item.id] ? 'text-on-surface-variant line-through' : 'text-on-surface'"
          >
            {{ item.label }}
          </span>
        </label>
        <p class="font-body-sm text-body-sm text-on-surface-variant pt-2">
          Отметки сохраняются только в этом браузере — общего чек-листа сборов пока нет ни в одном сервисе.
        </p>
      </div>
    </div>
  </div>
</template>
