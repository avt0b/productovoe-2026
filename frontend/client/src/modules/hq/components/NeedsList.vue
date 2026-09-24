<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import { NEED_KINDS, contactLink, tripDay, type Need, type Squad, type Trip } from '../data'

/**
 * Потребности без денег: нужны люди, нужно снаряжение. Помочь здесь — значит
 * поехать с отрядом или связаться с его штабом, поэтому у строки два пути:
 * к ближайшему выезду отряда и к его контакту.
 */
const props = defineProps<{
  needs: Need[]
  squads: Map<string, Squad>
  /** Ближайший выезд каждого отряда. */
  nextTrips: Map<string, Trip>
  /** Может ли человек править потребность этого отряда: командир или администратор. */
  canManage?: (squadId: string) => boolean
}>()

const emit = defineEmits<{ trip: [tripId: string]; edit: [need: Need] }>()

const rows = computed(() =>
  props.needs.map((need) => {
    const squad = props.squads.get(need.squad_id)
    const trip = props.nextTrips.get(need.squad_id) ?? null
    const day = trip ? tripDay(trip.starts_on) : null
    return {
      need,
      squad,
      trip,
      tripLabel: day ? `К выезду ${day.day} ${day.month}` : '',
      contact: contactLink(squad?.contact ?? ''),
      manage: props.canManage?.(need.squad_id) ?? false,
    }
  }),
)
</script>

<template>
  <ul class="flex flex-col gap-space-sm">
    <li
      v-for="{ need, squad, trip, tripLabel, contact, manage } in rows"
      :key="need.id"
      class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document"
    >
      <div class="flex items-start gap-space-sm">
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
          aria-hidden="true"
        >
          <MsIcon :name="NEED_KINDS[need.kind].icon" :size="20" />
        </span>
        <div class="flex min-w-0 flex-1 flex-col">
          <div class="flex items-center justify-between gap-space-xs">
            <p class="font-archival text-archival uppercase text-on-surface-variant">{{ NEED_KINDS[need.kind].title }}</p>
            <span class="truncate font-label-sm text-label-sm text-on-surface-variant">{{ squad?.region }}</span>
          </div>
          <h3 class="font-label-lg text-label-lg text-on-surface">{{ need.title }}</h3>
          <p class="font-body-sm text-body-sm text-on-surface-variant">{{ squad?.name }}</p>
          <p v-if="need.description" class="mt-space-xs font-body-sm text-body-sm text-on-surface-variant">{{ need.description }}</p>
        </div>
      </div>

      <div v-if="trip || contact || manage" class="flex flex-wrap gap-space-xs">
        <button
          v-if="manage"
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="emit('edit', need)"
        >
          <MsIcon name="edit" :size="18" />
          Изменить
        </button>
        <button
          v-if="trip"
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="emit('trip', trip.id)"
        >
          <MsIcon name="event" :size="18" />
          {{ tripLabel }}
        </button>
        <a
          v-if="contact"
          :href="contact.href"
          target="_blank"
          rel="noopener"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        >
          <MsIcon :name="contact.icon" :size="18" />
          {{ contact.label }}
        </a>
      </div>
      <!-- Контакт не похож ни на ссылку, ни на телефон — показываем как есть, человек разберётся. -->
      <p v-if="!contact && squad?.contact" class="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
        <MsIcon name="contact_phone" :size="18" class="shrink-0" />
        {{ squad.contact }}
      </p>
    </li>
  </ul>
</template>
