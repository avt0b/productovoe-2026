<script setup lang="ts">
import { computed, ref } from 'vue'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { FieldEvent } from '../data'

const props = defineProps<{ event: FieldEvent }>()

// Копия, а не сами данные: отметки в чек-листе — дело этого экрана, заглушка не должна меняться.
const checklist = ref(props.event.checklist.map((item) => ({ ...item })))
const signedUp = ref(false)

const readyCount = computed(() => checklist.value.filter((item) => item.done).length)

const seatsLabel = computed(
  () =>
    `Осталось ${props.event.seatsLeft} ${plural(props.event.seatsLeft, ['место', 'места', 'мест'])} из ${props.event.seatsTotal}`,
)
</script>

<template>
  <article class="flex flex-col gap-4 rounded-lg border border-field-line/40 bg-field-surface p-5 shadow-sm">
    <div class="flex items-center gap-2 font-label-md text-label-md text-field">
      <MsIcon name="calendar_month" :size="18" />
      <span>{{ event.when }}</span>
    </div>

    <div class="flex flex-col gap-1">
      <h3 class="font-headline-sm text-headline-sm font-bold text-on-surface">{{ event.title }}</h3>
      <p class="mt-1 flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface-variant">
        <MsIcon name="person" :size="18" class="text-field" />{{ event.leader }}
      </p>
    </div>

    <div class="flex flex-col gap-3 rounded-DEFAULT border border-field-muted/20 bg-field-surface-high p-4">
      <div class="flex items-center justify-between">
        <span class="font-label-md text-label-md font-bold uppercase tracking-wider text-field">Чек-лист новичка</span>
        <span class="font-label-sm text-label-sm text-field-muted">{{ readyCount }} из {{ checklist.length }} готово</span>
      </div>
      <ul class="flex flex-col gap-2.5">
        <li v-for="item in checklist" :key="item.id">
          <label class="flex cursor-pointer select-none items-center gap-3">
            <input v-model="item.done" type="checkbox" class="peer sr-only" />
            <span
              class="flex h-6 w-6 items-center justify-center rounded-md transition-colors peer-focus-visible:ring-2 peer-focus-visible:ring-primary"
              :class="item.done ? 'bg-field text-on-secondary' : 'bg-surface-container-highest text-transparent'"
            >
              <MsIcon name="check" :size="16" />
            </span>
            <span class="font-body-md text-body-md text-on-surface" :class="{ 'line-through opacity-70': item.done }">
              {{ item.title }}
            </span>
          </label>
        </li>
      </ul>
    </div>

    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-1.5 font-label-md text-label-md text-error">
        <MsIcon name="group" :size="18" />
        <span>{{ seatsLabel }}</span>
      </div>
      <span v-if="event.free" class="font-label-sm text-label-sm text-field-muted">Бесплатно</span>
    </div>

    <button
      type="button"
      class="flex w-full items-center justify-center gap-2 rounded-full bg-field px-6 py-3.5 font-label-lg text-label-lg text-on-secondary shadow-sm transition-all hover:brightness-105 active:scale-[0.98] disabled:opacity-90"
      :disabled="signedUp"
      @click="signedUp = true"
    >
      <MsIcon :name="signedUp ? 'check_circle' : 'how_to_reg'" :size="20" />
      <span>{{ signedUp ? 'Вы в экспедиции!' : 'Записаться волонтером' }}</span>
    </button>
  </article>
</template>
