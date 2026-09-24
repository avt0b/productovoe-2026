<script setup lang="ts">
import { Browser } from '@capacitor/browser'
import { Capacitor } from '@capacitor/core'
import { computed, onBeforeUnmount, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import { STATUS_LABELS, STATUS_STYLE, sourceIcon, type FindRecord, type FindStatus } from '../data'

const props = defineProps<{
  record: FindRecord
  /** Есть окно «Штаб» — «Готов помочь» ведёт к выездам отрядов. */
  canVolunteer: boolean
  /**
   * «Готов помочь» — главное действие экрана. Не главное, когда на экране уже
   * есть «Отметить место» для поисковика: главная кнопка на экране одна.
   */
  volunteerIsPrimary: boolean
  /** Администратор: может сменить стадию места. */
  canModerate: boolean
  /** Автор места или администратор: может уточнить сведения (`_ensure_can_edit` в map_service). */
  canEdit: boolean
  busy: boolean
}>()

defineEmits<{ volunteer: []; addData: []; edit: []; setStatus: [status: FindStatus] }>()

const STAGES: FindStatus[] = ['found', 'confirmed', 'raised']

/** Бейдж стадии — теми же ролями цвета, что метка на карте. */
const STAGE_BADGE: Record<FindStatus, string> = {
  found: 'bg-primary-fixed text-on-primary-fixed-variant',
  confirmed: 'bg-tertiary-fixed text-on-tertiary-fixed',
  raised: 'bg-secondary-container text-on-secondary-container',
}

const stageIndex = computed(() => STAGES.indexOf(props.record.status))

// --- координаты: скопировать и проложить путь ---

const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

async function copyCoordinates(): Promise<void> {
  try {
    await navigator.clipboard.writeText(`${props.record.lat}, ${props.record.lon}`)
    copied.value = true
    clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => (copied.value = false), 2000)
  } catch {
    // Буфер недоступен (старый WebView) — координаты и так выделяются целиком по тапу.
  }
}

onBeforeUnmount(() => clearTimeout(copiedTimer))

/**
 * Место обычно в поле за деревней — туда едут, поэтому маршрут на машине.
 * Откуда — Карты спросят сами: так не нужно просить геолокацию ради ссылки.
 */
async function openRoute(): Promise<void> {
  const url = `https://yandex.ru/maps/?rtext=~${props.record.lat},${props.record.lon}&rtt=auto`
  if (Capacitor.isNativePlatform()) await Browser.open({ url })
  else window.open(url, '_blank', 'noopener')
}
</script>

<template>
  <article class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <header class="flex flex-wrap items-center justify-between gap-space-xs">
      <span
        class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-label-md text-label-md"
        :class="STAGE_BADGE[record.status]"
      >
        <MsIcon :name="STATUS_STYLE[record.status].icon" :size="15" :filled="record.status !== 'found'" />
        {{ record.stage }}
      </span>
      <span
        v-if="record.unit"
        class="max-w-full truncate rounded-full bg-surface-container-high px-2.5 py-1 font-label-sm text-label-sm text-on-surface-variant"
      >
        {{ record.unit }}
      </span>
    </header>

    <div>
      <h3 class="font-headline-md text-headline-md text-on-surface">{{ record.title }}</h3>
      <p class="mt-0.5 font-body-sm text-body-sm text-on-surface-variant">{{ record.period }}</p>
    </div>

    <dl class="flex flex-col gap-space-sm rounded-xl bg-surface-container-low p-space-md">
      <div class="flex items-start gap-space-sm">
        <MsIcon name="pin_drop" :size="18" class="mt-0.5 shrink-0 text-primary" />
        <dt class="sr-only">Координаты</dt>
        <dd class="min-w-0 flex-1 select-all font-label-md text-label-md text-on-surface">{{ record.coordinates }}</dd>
        <button
          type="button"
          class="-my-1 flex shrink-0 items-center gap-1 rounded-full px-2 py-1 font-label-sm text-label-sm text-on-surface-variant transition-colors hover:bg-surface-container active:scale-95"
          :aria-label="copied ? 'Координаты скопированы' : 'Скопировать координаты'"
          @click="copyCoordinates"
        >
          <MsIcon :name="copied ? 'check' : 'content_copy'" :size="15" />
          <span aria-hidden="true">{{ copied ? 'Скопировано' : 'Копировать' }}</span>
        </button>
      </div>
      <div class="flex items-start gap-space-sm">
        <MsIcon :name="sourceIcon(record.source)" :size="18" class="mt-0.5 shrink-0 text-tertiary" />
        <dt class="sr-only">Источник</dt>
        <dd class="font-body-sm text-body-sm text-on-surface">{{ record.source }}</dd>
      </div>
      <div class="flex items-start gap-space-sm">
        <MsIcon name="history_edu" :size="18" class="mt-0.5 shrink-0 text-secondary" />
        <dt class="sr-only">Обстоятельства</dt>
        <dd class="font-body-sm text-body-sm text-on-surface-variant">{{ record.evidence }}</dd>
      </div>
    </dl>

    <!--
      Администратор ведёт место по стадиям кейса. Подложка выбранной стадии едет
      трансформацией, как вкладки на экране входа: видно, куда ушёл выбор.
    -->
    <div v-if="canModerate" class="flex flex-col gap-space-xs">
      <span class="font-archival text-archival uppercase text-on-surface-variant">Стадия · администратор</span>
      <div class="relative grid grid-cols-3 rounded-xl bg-surface-container p-1 text-center" role="radiogroup" aria-label="Стадия места">
        <span
          class="absolute inset-y-1 left-1 w-[calc((100%-8px)/3)] rounded-lg bg-surface-container-lowest shadow-float transition-transform duration-300 ease-out"
          :style="{ transform: `translateX(${stageIndex * 100}%)` }"
          aria-hidden="true"
        />
        <button
          v-for="stage in STAGES"
          :key="stage"
          type="button"
          role="radio"
          :aria-checked="record.status === stage"
          class="relative z-10 rounded-lg px-1 py-2 font-label-sm text-label-sm leading-tight transition-colors duration-200 disabled:cursor-default"
          :class="record.status === stage ? 'text-on-surface' : 'text-on-surface-variant'"
          :disabled="busy || record.status === stage"
          @click="$emit('setStatus', stage)"
        >
          {{ STATUS_LABELS[stage] }}
        </button>
      </div>
    </div>

    <div class="flex flex-col gap-space-sm">
      <button
        v-if="canVolunteer && volunteerIsPrimary"
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="$emit('volunteer')"
      >
        <MsIcon name="handshake" :size="18" />
        <span>Я готов помочь в подъёме</span>
      </button>

      <div class="flex flex-wrap gap-space-xs">
        <button
          v-if="canVolunteer && !volunteerIsPrimary"
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-secondary-container px-space-md py-2 font-label-md text-label-md text-on-secondary-container active:scale-95"
          @click="$emit('volunteer')"
        >
          <MsIcon name="handshake" :size="18" />
          Помочь в подъёме
        </button>
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="$emit('addData')"
        >
          <MsIcon name="upload_file" :size="18" />
          Дополнить данными
        </button>
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="openRoute"
        >
          <MsIcon name="directions_car" :size="18" />
          Маршрут к месту
        </button>
        <button
          v-if="canEdit"
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="$emit('edit')"
        >
          <MsIcon name="edit" :size="18" />
          Уточнить сведения
        </button>
      </div>
    </div>
  </article>
</template>
