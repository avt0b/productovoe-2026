<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import { STATUS_LABELS, type FindRecord, type FindStatus } from '../data'

defineProps<{
  record: FindRecord
  /** Есть окно «Штаб» — «Готов помочь» ведёт к выездам отрядов. */
  canVolunteer: boolean
  /** Модератор: может сменить стадию места. */
  canModerate: boolean
  busy: boolean
}>()

defineEmits<{ volunteer: []; addData: []; setStatus: [status: FindStatus] }>()

const STAGES: FindStatus[] = ['found', 'confirmed', 'raised']
</script>

<template>
  <div class="flex flex-col space-y-space-md rounded-lg bg-surface-container-lowest p-space-md shadow-md">
    <div class="flex flex-wrap items-center justify-between gap-space-xs">
      <span class="inline-flex items-center gap-1.5 rounded-full bg-tertiary-fixed px-3 py-1 font-label-md text-label-md text-on-tertiary-fixed">
        <MsIcon name="timelapse" :size="14" />
        {{ record.stage }}
      </span>
      <span
        v-if="record.unit"
        class="rounded-full bg-surface-container-high px-2.5 py-1 font-label-sm text-label-sm text-on-surface-variant"
      >
        {{ record.unit }}
      </span>
    </div>

    <div>
      <h3 class="font-headline-lg-mobile text-headline-lg-mobile leading-tight text-on-surface">{{ record.title }}</h3>
      <p class="mt-1 font-body-md text-body-md text-outline">{{ record.period }}</p>
    </div>

    <div class="space-y-space-xs rounded-lg bg-surface-container-low p-space-md">
      <div class="flex items-start gap-2 text-on-surface-variant">
        <MsIcon name="pin_drop" :size="18" class="mt-0.5 shrink-0 text-primary" />
        <span class="select-all font-body-sm text-body-sm">{{ record.coordinates }}</span>
      </div>
      <div class="flex items-start gap-2 pt-1 text-on-surface-variant">
        <MsIcon name="menu_book" :size="18" class="mt-0.5 shrink-0 text-secondary" />
        <span class="font-body-sm text-body-sm">{{ record.source }}</span>
      </div>
      <div class="flex items-start gap-2 pt-1 text-on-surface-variant">
        <MsIcon name="verified" :size="18" class="mt-0.5 shrink-0 text-tertiary" />
        <span class="font-body-sm text-body-sm leading-snug">{{ record.evidence }}</span>
      </div>
    </div>

    <!-- Модератор переводит место по стадиям кейса: обнаружено → подтверждено архивом → останки подняты. -->
    <div v-if="canModerate" class="flex flex-col gap-space-xs">
      <span class="font-label-md text-label-md text-on-surface">Стадия (модератор)</span>
      <div class="grid grid-cols-3 gap-1 rounded-DEFAULT bg-surface-container-low p-1">
        <button
          v-for="stage in STAGES"
          :key="stage"
          type="button"
          class="rounded-DEFAULT px-1 py-2 font-label-sm text-label-sm leading-tight transition-colors disabled:opacity-60"
          :class="record.status === stage ? 'bg-secondary text-on-secondary' : 'text-on-surface'"
          :disabled="busy || record.status === stage"
          @click="$emit('setStatus', stage)"
        >
          {{ STATUS_LABELS[stage] }}
        </button>
      </div>
    </div>

    <div class="flex flex-col gap-space-sm pt-1 sm:flex-row">
      <button
        v-if="canVolunteer"
        type="button"
        class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-primary px-space-md py-3 font-label-lg text-label-lg text-on-primary shadow-md transition-transform hover:opacity-95 active:scale-95"
        @click="$emit('volunteer')"
      >
        <MsIcon name="handshake" :size="20" />
        <span>Я готов помочь в выезде</span>
      </button>
      <button
        type="button"
        class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-secondary-container px-space-md py-3 font-label-lg text-label-lg text-on-secondary-container transition-transform hover:opacity-90 active:scale-95"
        @click="$emit('addData')"
      >
        <MsIcon name="upload_file" :size="20" />
        <span>Дополнить данными</span>
      </button>
    </div>
  </div>
</template>
