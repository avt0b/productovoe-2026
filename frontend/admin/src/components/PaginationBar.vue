<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber } from '@/lib'

const props = defineProps<{ total: number; limit: number; offset: number }>()
const emit = defineEmits<{ 'update:offset': [value: number] }>()

const page = computed(() => Math.floor(props.offset / props.limit) + 1)
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)))
const from = computed(() => (props.total === 0 ? 0 : props.offset + 1))
const to = computed(() => Math.min(props.offset + props.limit, props.total))

function go(delta: number): void {
  const next = props.offset + delta * props.limit
  if (next < 0 || next >= props.total) return
  emit('update:offset', next)
}
</script>

<template>
  <div
    class="flex flex-col items-center justify-between gap-space-3 rounded-b-xl bg-surface-container px-card-padding py-space-3 sm:flex-row"
  >
    <span class="font-label-archive-code text-label-archive-code uppercase text-on-surface-variant">
      Записи {{ formatNumber(from) }}–{{ formatNumber(to) }} из {{ formatNumber(total) }}
    </span>
    <div class="flex items-center gap-space-2">
      <button class="btn-secondary btn-sm" type="button" :disabled="page <= 1" @click="go(-1)">
        Назад
      </button>
      <span class="mono px-space-2 font-bold text-primary">стр. {{ page }} / {{ pages }}</span>
      <button class="btn-secondary btn-sm" type="button" :disabled="page >= pages" @click="go(1)">
        Вперёд
      </button>
    </div>
  </div>
</template>
