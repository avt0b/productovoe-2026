<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { formatDate, plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import { checklistItems, fetchTripRegistrations, type Squad, type Trip } from '../data'

const props = defineProps<{
  trip: Trip
  squad: Squad | undefined
  /** Записан ли человек. `null` — неизвестно (демо-режим). */
  registered: boolean | null
  busy: boolean
  /** Командир отряда или модератор: видит, сколько записалось. */
  canManage: boolean
}>()

defineEmits<{ register: []; cancel: [] }>()

/**
 * Отметки чек-листа — дело самого волонтёра, сервис их не хранит. Живут на
 * телефоне, по выезду: собрался наполовину, закрыл приложение — отметки на месте.
 */
const storageKey = computed(() => `marshruty.client.hq.checklist.${props.trip.id}`)
const items = computed(() => checklistItems(props.trip.checklist))
const done = ref<Set<string>>(new Set())

function readDone(): void {
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(storageKey.value) ?? '[]')
    done.value = new Set(Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string') : [])
  } catch {
    done.value = new Set()
  }
}

function toggle(item: string): void {
  const next = new Set(done.value)
  if (next.has(item)) next.delete(item)
  else next.add(item)
  done.value = next
  try {
    localStorage.setItem(storageKey.value, JSON.stringify([...next]))
  } catch {
    /* приватный режим — отметки проживут до закрытия */
  }
}

watch(storageKey, readDone, { immediate: true })

const readyCount = computed(() => items.value.filter((item) => done.value.has(item)).length)

/** Сколько записалось — сервис скажет только командиру. */
const registeredCount = ref<number | null>(null)
onMounted(async () => {
  if (!props.canManage) return
  try {
    const rows = await fetchTripRegistrations(props.trip.id)
    registeredCount.value = rows.filter((row) => row.status === 'registered').length
  } catch {
    registeredCount.value = null
  }
})

const seats = computed(() => {
  const capacity = props.trip.capacity
  if (registeredCount.value !== null) return `Записалось ${registeredCount.value} из ${capacity}`
  return `${capacity} ${plural(capacity, ['место', 'места', 'мест'])} на выезде`
})
</script>

<template>
  <article class="flex flex-col gap-4 rounded-lg border border-field-line/40 bg-field-surface p-5 shadow-sm">
    <div class="flex items-center gap-2 font-label-md text-label-md text-field">
      <MsIcon name="calendar_month" :size="18" />
      <span>{{ formatDate(trip.starts_on) }}</span>
      <span v-if="trip.location" class="truncate text-field-muted">• {{ trip.location }}</span>
    </div>

    <div class="flex flex-col gap-1">
      <h3 class="font-headline-sm text-headline-sm font-bold text-on-surface">{{ trip.title }}</h3>
      <p v-if="squad" class="mt-1 flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface-variant">
        <MsIcon name="flag" :size="18" class="text-field" />{{ squad.name }}
      </p>
      <p v-if="trip.description" class="mt-1 font-body-sm text-body-sm text-on-surface-variant">{{ trip.description }}</p>
    </div>

    <div v-if="items.length" class="flex flex-col gap-3 rounded-DEFAULT border border-field-muted/20 bg-field-surface-high p-4">
      <div class="flex items-center justify-between">
        <span class="font-label-md text-label-md font-bold uppercase tracking-wider text-field">Чек-лист новичка</span>
        <span class="font-label-sm text-label-sm text-field-muted">{{ readyCount }} из {{ items.length }} готово</span>
      </div>
      <ul class="flex flex-col gap-2.5">
        <li v-for="item in items" :key="item">
          <label class="flex cursor-pointer select-none items-center gap-3">
            <input type="checkbox" class="peer sr-only" :checked="done.has(item)" @change="toggle(item)" />
            <span
              class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md transition-colors peer-focus-visible:ring-2 peer-focus-visible:ring-primary"
              :class="done.has(item) ? 'bg-field text-on-secondary' : 'bg-surface-container-highest text-transparent'"
            >
              <MsIcon name="check" :size="16" />
            </span>
            <span class="font-body-md text-body-md text-on-surface" :class="{ 'line-through opacity-70': done.has(item) }">
              {{ item }}
            </span>
          </label>
        </li>
      </ul>
    </div>

    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-1.5 font-label-md text-label-md text-field">
        <MsIcon name="group" :size="18" />
        <span>{{ seats }}</span>
      </div>
      <span class="font-label-sm text-label-sm text-field-muted">Бесплатно</span>
    </div>

    <button
      v-if="!registered"
      type="button"
      class="flex w-full items-center justify-center gap-2 rounded-full bg-field px-6 py-3.5 font-label-lg text-label-lg text-on-secondary shadow-sm transition-all hover:brightness-105 active:scale-[0.98] disabled:opacity-70"
      :disabled="busy"
      @click="$emit('register')"
    >
      <MsIcon :name="busy ? 'progress_activity' : 'how_to_reg'" :size="20" :class="{ 'animate-spin': busy }" />
      <span>Записаться волонтёром</span>
    </button>
    <div v-else class="flex flex-col gap-space-xs">
      <p
        class="flex items-center justify-center gap-2 rounded-full bg-secondary-container px-6 py-3 font-label-lg text-label-lg text-on-secondary-container"
        role="status"
      >
        <MsIcon name="check_circle" :size="20" />
        Вы в экспедиции!
      </p>
      <button
        type="button"
        class="self-center font-label-md text-label-md text-on-surface-variant underline-offset-2 hover:underline disabled:opacity-60"
        :disabled="busy"
        @click="$emit('cancel')"
      >
        Отменить запись
      </button>
    </div>
  </article>
</template>
