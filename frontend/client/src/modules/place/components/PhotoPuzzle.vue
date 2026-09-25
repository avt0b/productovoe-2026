<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

/**
 * Пазл на перестановку: касаешься двух фрагментов — они меняются местами.
 * Не «пятнашки» с пустой клеткой — на маленьком экране пальцем целиться в
 * соседнюю с пустотой клетку неудобно, а любые два фрагмента — легко. Так же
 * собирается всегда, при любой перетасовке.
 */
const props = withDefaults(defineProps<{ photoUrl: string; grid?: number }>(), { grid: 3 })
const emit = defineEmits<{ solved: [] }>()

const total = computed(() => props.grid * props.grid)

function shuffledOrder(count: number): number[] {
  const order = Array.from({ length: count }, (_, index) => index)
  // Пока не перемешалось по-настоящему: иначе изредка пазл открывался бы уже собранным.
  do {
    for (let i = order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[order[i], order[j]] = [order[j], order[i]]
    }
  } while (count > 1 && order.every((value, index) => value === index))
  return order
}

const order = ref<number[]>(shuffledOrder(total.value))
const selected = ref<number | null>(null)
const solved = computed(() => order.value.every((value, index) => value === index))

watch(solved, (value) => {
  if (value) emit('solved')
})

// Новое фото места — новый пазл, с начала.
watch(
  () => props.photoUrl,
  () => {
    order.value = shuffledOrder(total.value)
    selected.value = null
  },
)

function tap(position: number): void {
  if (solved.value) return
  if (selected.value === null) {
    selected.value = position
    return
  }
  if (selected.value === position) {
    selected.value = null
    return
  }
  const next = [...order.value]
  ;[next[selected.value], next[position]] = [next[position], next[selected.value]]
  order.value = next
  selected.value = null
}

function restart(): void {
  order.value = shuffledOrder(total.value)
  selected.value = null
}

/** Откуда у фрагмента взят кусок фотографии — координата в проценты фона плитки. */
function piecePosition(pieceIndex: number): string {
  const row = Math.floor(pieceIndex / props.grid)
  const col = pieceIndex % props.grid
  const step = props.grid > 1 ? 100 / (props.grid - 1) : 0
  return `${col * step}% ${row * step}%`
}
</script>

<template>
  <div class="flex flex-col gap-space-sm">
    <div
      class="relative grid aspect-square w-full gap-0.5 overflow-hidden rounded-2xl bg-surface-container-high shadow-document"
      :style="{ gridTemplateColumns: `repeat(${grid}, 1fr)`, gridTemplateRows: `repeat(${grid}, 1fr)` }"
    >
      <button
        v-for="(piece, position) in order"
        :key="position"
        type="button"
        class="relative bg-cover transition-transform duration-150"
        :style="{
          backgroundImage: `url(${photoUrl})`,
          backgroundSize: `${grid * 100}% ${grid * 100}%`,
          backgroundPosition: piecePosition(piece),
        }"
        :class="selected === position ? 'z-10 scale-95 ring-4 ring-inset ring-primary' : 'ring-1 ring-inset ring-black/10'"
        :disabled="solved"
        :aria-label="`Фрагмент ${position + 1} из ${total}`"
        @click="tap(position)"
      />

      <div
        v-if="solved"
        class="absolute inset-0 flex flex-col items-center justify-center gap-space-xs bg-night/55 text-white backdrop-blur-sm"
      >
        <MsIcon name="celebration" :size="32" filled />
        <p class="font-label-lg text-label-lg">Пазл собран!</p>
      </div>
    </div>

    <p v-if="!solved" class="flex items-center justify-center gap-1.5 text-center font-label-sm text-label-sm text-on-surface-variant">
      <MsIcon name="touch_app" :size="16" />
      Коснитесь двух фрагментов, чтобы поменять их местами
    </p>

    <button
      v-else
      type="button"
      class="flex items-center justify-center gap-1.5 self-center rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
      @click="restart"
    >
      <MsIcon name="replay" :size="18" />
      Собрать ещё раз
    </button>
  </div>
</template>
