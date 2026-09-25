<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

/**
 * Пазл на перестановку: касаешься двух фрагментов — они меняются местами.
 * Не «пятнашки» с пустой клеткой — на маленьком экране пальцем целиться в
 * соседнюю с пустотой клетку неудобно, а любые два фрагмента — легко. Так же
 * собирается всегда, при любой перетасовке.
 *
 * Форма фрагментов — настоящий пазл с зубчиками, а не квадраты: у каждой
 * внутренней грани сетки — свой «замочек» (выпуклость у одного соседа,
 * такая же по форме выемка у другого). Форма зависит только от МЕСТА в
 * сетке (не меняется при перестановке), картинка внутри — от того, какой
 * фрагмент туда сейчас передвинут.
 */
const props = withDefaults(defineProps<{ photoUrl: string; grid?: number }>(), { grid: 4 })
const emit = defineEmits<{ solved: [] }>()

const total = computed(() => props.grid * props.grid)
const uid = useId()

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

/**
 * Форма зубчиков — фиксированная на весь пазл, не пересчитывается при
 * перестановке фрагментов. `hEdge`/`vEdge` — в какую сторону (в единицах
 * доли стороны клетки) выгибается общая граница между соседями; у одной и
 * той же границы оба соседа рисуют ровно одну и ту же кривую — поэтому
 * выступ у одного всегда впритык совпадает с выемкой у другого.
 */
const tabs = computed(() => {
  const n = props.grid
  const rand = (): 1 | -1 => (Math.random() < 0.5 ? 1 : -1)
  const hEdge: (1 | -1)[][] = Array.from({ length: n - 1 }, () => Array.from({ length: n }, rand))
  const vEdge: (1 | -1)[][] = Array.from({ length: n - 1 }, () => Array.from({ length: n }, rand))
  return { hEdge, vEdge }
})

/** Радиус «замочка» — доля стороны клетки. Больше — заметнее зубчик, но соседние могут задевать друг друга. */
const TAB_RADIUS_FRACTION = 0.2

/** Путь границы клетки (r,c) в долях 0..1 всей картинки — для `clipPathUnits="objectBoundingBox"`. */
function cellPath(r: number, c: number): string {
  const n = props.grid
  const s = 1 / n
  const rr = s * TAB_RADIUS_FRACTION
  const { hEdge, vEdge } = tabs.value
  const x0 = c * s
  const x1 = (c + 1) * s
  const y0 = r * s
  const y1 = (r + 1) * s
  const mid = (a: number, b: number) => (a + b) / 2
  const arc = (rad: number, sweep: 0 | 1, x: number, y: number) => `A ${rad} ${rad} 0 0 ${sweep} ${x} ${y}`

  // Верх: слева направо.
  const top =
    r === 0
      ? `L ${x1} ${y0}`
      : `L ${mid(x0, x1) - rr} ${y0} ${arc(rr, hEdge[r - 1][c] === 1 ? 1 : 0, mid(x0, x1) + rr, y0)} L ${x1} ${y0}`

  // Право: сверху вниз.
  const right =
    c === n - 1
      ? `L ${x1} ${y1}`
      : `L ${x1} ${mid(y0, y1) - rr} ${arc(rr, vEdge[c][r] === -1 ? 1 : 0, x1, mid(y0, y1) + rr)} L ${x1} ${y1}`

  // Низ: справа налево.
  const bottom =
    r === n - 1
      ? `L ${x0} ${y1}`
      : `L ${mid(x0, x1) + rr} ${y1} ${arc(rr, hEdge[r][c] === 1 ? 0 : 1, mid(x0, x1) - rr, y1)} L ${x0} ${y1}`

  // Лево: снизу вверх, обратно к старту.
  const left =
    c === 0
      ? `L ${x0} ${y0}`
      : `L ${x0} ${mid(y0, y1) + rr} ${arc(rr, vEdge[c - 1][r] === 1 ? 1 : 0, x0, mid(y0, y1) - rr)} L ${x0} ${y0}`

  return `M ${x0} ${y0} ${top} ${right} ${bottom} ${left} Z`
}

interface Cell {
  clipId: string
  d: string
}

const cells = computed<Cell[]>(() => {
  const n = props.grid
  const list: Cell[] = []
  for (let position = 0; position < n * n; position++) {
    const r = Math.floor(position / n)
    const c = position % n
    list.push({ clipId: `${uid}-piece-${position}`, d: cellPath(r, c) })
  }
  return list
})
</script>

<template>
  <div class="flex flex-col gap-space-sm">
    <div class="relative aspect-square w-full overflow-hidden rounded-2xl bg-surface-container-high shadow-document">
      <!-- Формы фрагментов — только для clip-path, сама SVG не рисуется. -->
      <svg class="absolute h-0 w-0" aria-hidden="true">
        <defs>
          <clipPath v-for="cell in cells" :id="cell.clipId" :key="cell.clipId" clipPathUnits="objectBoundingBox">
            <path :d="cell.d" />
          </clipPath>
        </defs>
      </svg>

      <button
        v-for="(piece, position) in order"
        :key="position"
        type="button"
        class="absolute inset-0 bg-cover transition-[transform,filter] duration-150"
        :style="{
          clipPath: `url(#${cells[position].clipId})`,
          backgroundImage: `url(${photoUrl})`,
          backgroundSize: `${grid * 100}% ${grid * 100}%`,
          backgroundPosition: piecePosition(piece),
        }"
        :class="selected === position ? 'z-10 scale-105 brightness-110 drop-shadow-lg' : 'drop-shadow-sm'"
        :disabled="solved"
        :aria-label="`Фрагмент ${position + 1} из ${total}`"
        @click="tap(position)"
      />

      <!-- Контурные линии поверх картинки — без них зубчики на однотонных участках почти не видны. -->
      <svg class="pointer-events-none absolute inset-0 h-full w-full" viewBox="0 0 1 1" preserveAspectRatio="none" aria-hidden="true">
        <path v-for="cell in cells" :key="cell.clipId" :d="cell.d" fill="none" stroke="rgba(0,0,0,0.35)" stroke-width="0.006" />
      </svg>

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
