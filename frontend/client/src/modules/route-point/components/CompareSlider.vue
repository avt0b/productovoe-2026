<script setup lang="ts">
import { ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

defineProps<{
  archiveImage: string
  archiveLabel: string
  modernImage: string
  modernLabel: string
  source: string
}>()

const MIN = 5
const MAX = 95
const KEY_STEP = 5

/** Сколько процентов ширины занимает архивный кадр слева. */
const position = ref(50)
const container = ref<HTMLElement | null>(null)
let dragging = false

function moveTo(clientX: number): void {
  const rect = container.value?.getBoundingClientRect()
  if (!rect || rect.width === 0) return
  const percent = ((clientX - rect.left) / rect.width) * 100
  position.value = Math.min(MAX, Math.max(MIN, percent))
}

function onPointerDown(event: PointerEvent): void {
  dragging = true
  // Захват указателя: разделитель не «отпускается», если палец ушёл за край карточки.
  container.value?.setPointerCapture(event.pointerId)
  moveTo(event.clientX)
}

function onPointerMove(event: PointerEvent): void {
  if (dragging) moveTo(event.clientX)
}

function onPointerUp(): void {
  dragging = false
}

function onKey(event: KeyboardEvent): void {
  if (event.key === 'ArrowLeft') position.value = Math.max(MIN, position.value - KEY_STEP)
  else if (event.key === 'ArrowRight') position.value = Math.min(MAX, position.value + KEY_STEP)
  else return
  event.preventDefault()
}
</script>

<template>
  <div class="relative w-full select-none overflow-hidden rounded-lg bg-surface-container-low shadow-sm">
    <div
      ref="container"
      class="relative h-64 w-full touch-none overflow-hidden"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <!-- Сегодня — во всю ширину -->
      <img :src="modernImage" alt="" class="pointer-events-none absolute inset-0 h-full w-full object-cover" />
      <div
        class="absolute right-3 top-3 z-10 rounded-full bg-surface/85 px-2.5 py-1 font-label-sm text-label-sm text-on-surface shadow-sm backdrop-blur-md"
      >
        {{ modernLabel }}
      </div>

      <!--
        Архивный кадр той же ширины, обрезанный справа. Обрезка, а не сужение
        слоя: иначе картинка сжималась бы вместе с разделителем, и «тогда»
        переставало бы совпадать с «сейчас» по месту.
      -->
      <img
        :src="archiveImage"
        alt=""
        class="pointer-events-none absolute inset-0 h-full w-full object-cover"
        :style="{ clipPath: `inset(0 ${100 - position}% 0 0)` }"
      />
      <div
        class="absolute left-3 top-3 z-10 rounded-full bg-surface-dim/90 px-2.5 py-1 font-label-sm text-label-sm text-on-surface shadow-sm backdrop-blur-md"
      >
        {{ archiveLabel }}
      </div>

      <!-- Разделитель -->
      <div
        class="absolute bottom-0 top-0 z-20 -ml-4 flex w-8 cursor-ew-resize items-center justify-center"
        :style="{ left: `${position}%` }"
        role="slider"
        tabindex="0"
        aria-label="Сравнение архивного кадра и сегодняшнего вида"
        :aria-valuemin="MIN"
        :aria-valuemax="MAX"
        :aria-valuenow="Math.round(position)"
        @keydown="onKey"
      >
        <div class="h-full w-1 bg-surface-container-lowest shadow-md" />
        <div class="absolute flex h-8 w-8 items-center justify-center rounded-full bg-surface-container-lowest text-primary shadow-md">
          <MsIcon name="drag_indicator" :size="18" />
        </div>
      </div>

      <div class="pointer-events-none absolute bottom-3 left-3 right-3 z-10 flex items-center justify-between">
        <span class="rounded-full bg-surface/90 px-3 py-1 font-label-sm text-label-sm text-on-surface-variant shadow-sm backdrop-blur-md">
          {{ source }}
        </span>
        <span class="rounded-full bg-primary-container px-2.5 py-1 font-label-sm text-label-sm text-on-primary-container shadow-sm">
          Сравнить эпоху
        </span>
      </div>
    </div>
  </div>
</template>
