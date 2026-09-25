<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { plural } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'

import { checklistItems, fetchTripRegistrations, isCancelled, tripDay, type Squad, type Trip } from '../data'

const props = defineProps<{
  trip: Trip
  squad: Squad | undefined
  /** Записан ли человек. `null` — неизвестно (демо-режим). */
  registered: boolean | null
  busy: boolean
  /** Запись или отписка не прошла — текст ошибки сервиса. */
  error?: string | null
  /** Командир отряда или администратор: видит, сколько записалось. */
  canManage: boolean
  /** Сюда только что привели с другого блока — карточку надо заметить. */
  focused?: boolean
}>()

defineEmits<{ register: []; cancel: []; edit: []; chat: [] }>()

const day = computed(() => tripDay(props.trip.starts_on))
const cancelled = computed(() => isCancelled(props.trip))

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
const readyPercent = computed(() => (items.value.length ? Math.round((readyCount.value / items.value.length) * 100) : 0))

/** Записавшемуся чек-лист нужен сразу — остальным он раскрывается по нажатию. */
const checklistOpen = ref(props.registered === true)
watch(
  () => props.registered,
  (registered) => {
    if (registered) checklistOpen.value = true
  },
)

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
const seatsPercent = computed(() =>
  registeredCount.value === null ? null : Math.min(100, Math.round((registeredCount.value / Math.max(1, props.trip.capacity)) * 100)),
)
</script>

<template>
  <article
    class="flex scroll-mt-space-md flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document ring-secondary/60 transition-shadow duration-300"
    :class="{ 'ring-2': focused }"
  >
    <div class="flex items-start gap-space-sm">
      <!-- Листок календаря: день выезда виден раньше названия. -->
      <div class="flex w-14 shrink-0 flex-col items-center overflow-hidden rounded-2xl bg-surface-container-low text-center" aria-hidden="true">
        <span class="w-full bg-secondary py-0.5 font-label-sm text-label-sm uppercase text-on-secondary">{{ day.month }}</span>
        <span class="font-headline-md text-headline-md text-on-surface">{{ day.day }}</span>
        <span class="pb-1 font-label-sm text-label-sm text-on-surface-variant">{{ day.weekday }}</span>
      </div>
      <div class="flex min-w-0 flex-1 flex-col">
        <p class="font-archival text-archival uppercase" :class="cancelled ? 'text-on-surface-variant' : 'text-secondary'">
          {{ cancelled ? 'Отменён' : day.relative }}
        </p>
        <h3 class="font-headline-sm text-headline-sm" :class="cancelled ? 'text-on-surface-variant line-through' : 'text-on-surface'">
          {{ trip.title }}
        </h3>
        <p class="sr-only">{{ day.long }}</p>
        <p v-if="squad" class="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
          <MsIcon name="flag" :size="15" class="shrink-0 text-secondary" />
          <span class="truncate">{{ squad.name }}</span>
        </p>
        <p v-if="trip.location" class="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
          <MsIcon name="location_on" :size="15" class="shrink-0 text-secondary" />
          <span class="truncate">{{ trip.location }}</span>
        </p>
      </div>
    </div>

    <p v-if="trip.description" class="font-body-sm text-body-sm text-on-surface-variant">{{ trip.description }}</p>

    <div v-if="!cancelled" class="flex flex-col gap-space-xs">
      <div class="flex items-center justify-between gap-space-sm">
        <span class="flex items-center gap-1 font-label-md text-label-md text-secondary">
          <MsIcon name="group" :size="18" />
          {{ seats }}
        </span>
        <span class="font-label-sm text-label-sm text-on-surface-variant">Бесплатно</span>
      </div>
      <div
        v-if="seatsPercent !== null"
        class="h-1.5 w-full overflow-hidden rounded-full bg-surface-container-high"
        role="progressbar"
        :aria-valuenow="seatsPercent"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-label="Сколько мест занято"
      >
        <div class="h-full rounded-full bg-secondary transition-[width] duration-500 ease-out" :style="{ width: `${seatsPercent}%` }" />
      </div>
    </div>

    <div v-if="items.length && !cancelled" class="overflow-hidden rounded-2xl bg-surface-container-low">
      <button
        type="button"
        class="flex w-full items-center justify-between gap-space-sm px-space-sm py-2 text-left"
        :aria-expanded="checklistOpen"
        @click="checklistOpen = !checklistOpen"
      >
        <span class="flex items-center gap-space-xs font-label-md text-label-md text-on-surface">
          <MsIcon name="checklist" :size="18" class="text-secondary" />
          Чек-лист подготовки
        </span>
        <span class="flex items-center gap-1 font-label-sm text-label-sm" :class="readyCount === items.length ? 'text-secondary' : 'text-on-surface-variant'">
          {{ readyCount === items.length ? 'Всё готово' : `${readyCount} из ${items.length}` }}
          <MsIcon name="expand_more" :size="18" class="transition-transform duration-300" :class="{ 'rotate-180': checklistOpen }" />
        </span>
      </button>
      <div class="h-0.5 w-full bg-surface-container-high" aria-hidden="true">
        <div class="h-full bg-secondary transition-[width] duration-300 ease-out" :style="{ width: `${readyPercent}%` }" />
      </div>
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="checklistOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!checklistOpen"
      >
        <div class="overflow-hidden">
          <ul class="flex flex-col gap-space-xs p-space-sm">
            <li v-for="item in items" :key="item">
              <label class="flex cursor-pointer select-none items-center gap-space-sm py-0.5">
                <input type="checkbox" class="peer sr-only" :checked="done.has(item)" @change="toggle(item)" />
                <span
                  class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md transition-colors duration-200 peer-focus-visible:ring-2 peer-focus-visible:ring-secondary"
                  :class="done.has(item) ? 'bg-secondary text-on-secondary' : 'border border-outline-variant bg-surface-container-lowest text-transparent'"
                >
                  <MsIcon name="check" :size="15" />
                </span>
                <span
                  class="font-body-md text-body-md transition-colors duration-200"
                  :class="done.has(item) ? 'text-on-surface-variant line-through' : 'text-on-surface'"
                >
                  {{ item }}
                </span>
              </label>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Отменённый выезд: вместо записи — почему отменили. Чат остаётся: записавшимся есть что обсудить. -->
    <div v-if="cancelled" class="flex items-start gap-space-sm rounded-2xl bg-surface-container-high p-space-sm" role="status">
      <MsIcon name="event_busy" :size="20" class="mt-0.5 shrink-0 text-on-surface-variant" />
      <div class="min-w-0">
        <p class="font-label-lg text-label-lg text-on-surface">Выезд отменён</p>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          {{ trip.cancel_reason ? `Причина: ${trip.cancel_reason}` : 'Командир отряда отменил выезд. Следите за новыми датами.' }}
        </p>
      </div>
    </div>

    <div v-if="canManage" class="flex flex-wrap items-center justify-center gap-space-xs">
      <!-- У отменённого выезда править нечего — окно остаётся ради удаления. -->
      <button
        type="button"
        class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="$emit('edit')"
      >
        <MsIcon :name="cancelled ? 'delete' : 'edit'" :size="18" />
        {{ cancelled ? 'Удалить выезд' : 'Изменить выезд' }}
      </button>
      <button
        type="button"
        class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="$emit('chat')"
      >
        <MsIcon name="chat" :size="18" />
        Чат выезда
      </button>
    </div>

    <!-- У отменённого выезда причину уже объясняет плашка выше — второй раз «Выезд отменён» не пишем. -->
    <InlineNotice v-if="error && !cancelled" tone="error">{{ error }}</InlineNotice>

    <template v-if="cancelled">
      <button
        v-if="registered && !canManage"
        type="button"
        class="flex items-center gap-space-xs self-center rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="$emit('chat')"
      >
        <MsIcon name="chat" :size="18" />
        Чат выезда
      </button>
    </template>
    <button
      v-else-if="!registered"
      type="button"
      class="flex w-full items-center justify-center gap-space-xs rounded-full bg-secondary px-space-md py-2.5 font-label-lg text-label-lg text-on-secondary transition-all hover:brightness-105 active:scale-[0.99] disabled:opacity-70"
      :disabled="busy"
      @click="$emit('register')"
    >
      <MsIcon :name="busy ? 'progress_activity' : 'how_to_reg'" :size="18" :class="{ 'animate-spin': busy }" />
      Записаться волонтёром
    </button>
    <div v-else class="flex flex-col gap-space-xs">
      <p
        class="flex items-center justify-center gap-space-xs rounded-full bg-secondary-container px-space-md py-2.5 font-label-lg text-label-lg text-on-secondary-container"
        role="status"
      >
        <MsIcon name="check_circle" :size="18" filled />
        Вы в экспедиции!
      </p>
      <div class="flex items-center justify-center gap-space-sm">
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="$emit('chat')"
        >
          <MsIcon name="chat" :size="18" />
          Чат выезда
        </button>
        <button
          type="button"
          class="font-label-md text-label-md text-on-surface-variant underline-offset-2 hover:underline disabled:opacity-60"
          :disabled="busy"
          @click="$emit('cancel')"
        >
          Отменить запись
        </button>
      </div>
    </div>
  </article>
</template>
