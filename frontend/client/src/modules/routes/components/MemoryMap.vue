<script setup lang="ts">
import { ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { MapPin } from '../data'

/**
 * Нарисованная карта из макета.
 *
 * Холст держит пропорции макета (390×460), а метки ставятся в процентах от
 * него, — поэтому на экране любой ширины метка остаётся на своей тропе. Это
 * временная карта: когда подключим MapLibre, заменится этот компонент, а
 * метки придут из `map_service` в тех же полях.
 */
const selected = defineModel<string | null>('selected', { required: true })

defineProps<{
  pins: MapPin[]
  routeLabel: string
  canOpenAr: boolean
}>()

defineEmits<{ 'open-ar': [] }>()

const CANVAS_WIDTH = 390
const CANVAS_HEIGHT = 460
const ZOOM_STEP = 0.2
const ZOOM_MIN = 1
const ZOOM_MAX = 1.8

const zoom = ref(1)

function position(pin: MapPin): Record<string, string> {
  return {
    left: `${(pin.x / CANVAS_WIDTH) * 100}%`,
    top: `${(pin.y / CANVAS_HEIGHT) * 100}%`,
  }
}

function zoomBy(delta: number): void {
  zoom.value = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round((zoom.value + delta) * 10) / 10))
}
</script>

<template>
  <div class="relative w-full select-none overflow-hidden bg-map-paper">
    <div
      class="relative aspect-[390/460] w-full origin-center transition-transform duration-300"
      :style="{ transform: `scale(${zoom})` }"
    >
      <svg
        class="pointer-events-none absolute inset-0 h-full w-full"
        viewBox="0 0 390 460"
        fill="none"
        aria-hidden="true"
      >
        <defs>
          <pattern id="map-grid-dots" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
            <circle cx="2" cy="2" r="1" class="fill-map-grid" fill-opacity="0.6" />
          </pattern>
          <linearGradient id="map-river" x1="0%" y1="0%" x2="100%" y2="100%" class="text-map-river">
            <stop offset="0%" stop-color="currentColor" stop-opacity="0.6" />
            <stop offset="50%" stop-color="currentColor" stop-opacity="0.85" />
            <stop offset="100%" stop-color="currentColor" stop-opacity="0.55" />
          </linearGradient>
        </defs>

        <rect width="100%" height="100%" fill="url(#map-grid-dots)" />

        <!-- Горизонтали -->
        <g class="stroke-map-grid" stroke-width="1.5">
          <path d="M-20 60 C80 40, 160 90, 240 70 C320 50, 360 80, 420 65" stroke-dasharray="3 3" />
          <path d="M-30 140 C60 110, 140 180, 260 150 C340 120, 390 160, 430 145" stroke-dasharray="4 2" />
          <path d="M-10 230 C90 200, 170 270, 280 230 C360 210, 400 240, 430 220" stroke-dasharray="3 3" />
          <path d="M-20 330 C70 310, 150 370, 250 340 C350 320, 390 350, 420 335" stroke-dasharray="4 2" />
        </g>

        <!-- Лес -->
        <g class="fill-map-forest">
          <path d="M40 80 C70 60, 110 75, 125 105 C135 130, 110 160, 75 165 C45 170, 20 145, 25 115 Z" fill-opacity="0.9" />
          <path d="M260 210 C295 195, 340 205, 355 235 C370 265, 345 295, 310 300 C275 305, 245 280, 250 245 Z" fill-opacity="0.85" />
          <path d="M280 40 C310 25, 360 30, 375 60 C385 85, 360 110, 335 115 C305 120, 275 105, 275 75 Z" fill-opacity="0.6" />
        </g>

        <!-- Река -->
        <path
          d="M-20 280 C60 290, 90 250, 140 220 C190 190, 210 140, 270 120 C320 100, 360 110, 420 90"
          stroke="url(#map-river)"
          stroke-width="14"
          stroke-linecap="round"
        />
        <path
          d="M-20 280 C60 290, 90 250, 140 220 C190 190, 210 140, 270 120 C320 100, 360 110, 420 90"
          class="stroke-white"
          stroke-width="2"
          stroke-dasharray="12 18"
          stroke-linecap="round"
          stroke-opacity="0.5"
        />

        <!-- Маршрут и следы -->
        <path
          d="M78 285 C95 240, 140 230, 175 185 C205 145, 250 140, 292 105"
          class="stroke-secondary"
          stroke-width="3.5"
          stroke-dasharray="6 6"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <g class="fill-secondary" opacity="0.65">
          <g transform="translate(112, 235) rotate(-35)">
            <ellipse cx="0" cy="0" rx="2.5" ry="5" />
            <ellipse cx="6" cy="-4" rx="2.5" ry="5" />
          </g>
          <g transform="translate(225, 150) rotate(-42)">
            <ellipse cx="0" cy="0" rx="2.5" ry="5" />
            <ellipse cx="6" cy="-4" rx="2.5" ry="5" />
          </g>
        </g>
      </svg>

      <!-- Метки -->
      <button
        v-for="pin in pins"
        :key="pin.id"
        type="button"
        class="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
        :class="selected === pin.id ? 'z-30' : pin.kind === 'you' ? 'z-20' : 'z-10'"
        :style="position(pin)"
        :aria-label="pin.title"
        :aria-pressed="selected === pin.id"
        @click="selected = pin.id"
      >
        <!-- Выбранная метка -->
        <template v-if="selected === pin.id && pin.kind !== 'you'">
          <div class="relative flex items-center justify-center">
            <span class="absolute h-14 w-14 animate-pulse rounded-full bg-primary-fixed-dim/70" />
            <div
              class="flex h-12 w-12 scale-105 items-center justify-center rounded-full bg-primary text-on-primary shadow-lg shadow-primary/35 ring-4 ring-surface-container-lowest"
            >
              <MsIcon name="flag" />
            </div>
          </div>
          <div class="mt-1.5 flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-on-primary shadow-md shadow-primary/25">
            <span class="h-1.5 w-1.5 rounded-full bg-tertiary-fixed" />
            <span class="font-label-sm text-label-sm">{{ pin.title }}</span>
          </div>
        </template>

        <!-- Вы здесь -->
        <template v-else-if="pin.kind === 'you'">
          <div class="relative flex items-center justify-center">
            <span class="absolute h-8 w-8 animate-ping rounded-full bg-secondary-fixed opacity-75" />
            <div class="flex h-7 w-7 items-center justify-center rounded-full bg-surface-container-lowest text-secondary shadow-md">
              <div class="h-3.5 w-3.5 rounded-full bg-secondary" />
            </div>
          </div>
          <div class="mt-1 rounded-full bg-surface-container-lowest/90 px-2 py-0.5 shadow-sm backdrop-blur-md">
            <span class="font-label-sm text-label-sm text-on-surface">{{ pin.title }}</span>
          </div>
        </template>

        <!-- Памятное место и рубеж -->
        <template v-else>
          <div
            class="flex h-10 w-10 items-center justify-center rounded-full shadow-lg transition-transform hover:scale-110"
            :class="
              pin.kind === 'memorial'
                ? 'bg-secondary text-on-secondary shadow-secondary/35'
                : 'bg-tertiary text-on-tertiary shadow-tertiary/30'
            "
          >
            <MsIcon :name="pin.kind === 'memorial' ? 'security' : 'star'" :size="20" :filled="pin.kind === 'battle'" />
          </div>
          <div class="mt-1.5 max-w-32 rounded-xl bg-surface-container-lowest/95 px-2.5 py-1 text-center shadow-sm backdrop-blur-sm">
            <p class="font-label-sm text-label-sm leading-tight text-on-surface">{{ pin.title }}</p>
            <p v-if="pin.subtitle" class="mt-0.5 font-body-sm text-label-sm font-normal leading-none text-outline">
              {{ pin.subtitle }}
            </p>
          </div>
        </template>
      </button>
    </div>

    <!-- Управление картой -->
    <div class="absolute right-margin top-space-md z-30 flex flex-col gap-space-xs">
      <div class="flex flex-col items-center overflow-hidden rounded-full bg-surface-container-lowest/95 shadow-float backdrop-blur-md">
        <button
          type="button"
          aria-label="Приблизить"
          class="flex h-10 w-10 items-center justify-center text-on-surface transition-colors hover:bg-surface-container disabled:opacity-40"
          :disabled="zoom >= ZOOM_MAX"
          @click="zoomBy(ZOOM_STEP)"
        >
          <MsIcon name="add" :size="20" />
        </button>
        <div class="h-px w-5 bg-surface-container" />
        <button
          type="button"
          aria-label="Отдалить"
          class="flex h-10 w-10 items-center justify-center text-on-surface transition-colors hover:bg-surface-container disabled:opacity-40"
          :disabled="zoom <= ZOOM_MIN"
          @click="zoomBy(-ZOOM_STEP)"
        >
          <MsIcon name="remove" :size="20" />
        </button>
      </div>
      <button
        type="button"
        aria-label="AR-режим"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-lowest/95 text-tertiary shadow-float backdrop-blur-md transition-all hover:scale-105 disabled:opacity-40"
        :disabled="!canOpenAr"
        @click="$emit('open-ar')"
      >
        <MsIcon name="view_in_ar" :size="20" />
      </button>
      <button
        type="button"
        aria-label="Центрировать карту"
        class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-lowest/95 text-secondary shadow-float backdrop-blur-md transition-all hover:scale-105"
        @click="zoom = ZOOM_MIN"
      >
        <MsIcon name="my_location" :size="20" />
      </button>
    </div>

    <div class="absolute bottom-space-md left-margin z-20">
      <div class="flex items-center gap-1.5 rounded-full bg-surface-container-lowest/90 px-3 py-1.5 shadow-sm backdrop-blur-md">
        <MsIcon name="nature" :size="16" class="text-secondary" />
        <span class="font-label-sm text-label-sm font-medium text-on-surface-variant">{{ routeLabel }}</span>
      </div>
    </div>
  </div>
</template>
