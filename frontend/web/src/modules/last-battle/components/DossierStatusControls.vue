<script setup>
import { ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as lastStandApi from '../api.js'

const props = defineProps({
  point: { type: Object, required: true },
})
const emit = defineEmits(['updated'])

const { session } = useAuthSession()

// Менять статус может только модератор (или is_root) — так же решает и бэкенд.
const STEPS = [
  { id: 'discovered', label: 'Обнаружено' },
  { id: 'archive_confirmed', label: 'Подтверждено архивом' },
  { id: 'remains_raised', label: 'Останки подняты' },
]

const pending = ref(null)
const error = ref('')

watch(
  () => props.point?.id,
  () => {
    pending.value = null
    error.value = ''
  },
)

async function setStatus(nextStatus) {
  if (nextStatus === props.point.status) return
  pending.value = nextStatus
  error.value = ''
  try {
    const updated = await lastStandApi.setLastStandStatus(session.accessToken, props.point.id, nextStatus)
    emit('updated', updated)
  } catch (err) {
    error.value = err.detail ?? 'Не удалось изменить статус'
  } finally {
    pending.value = null
  }
}
</script>

<template>
  <div class="flex flex-col gap-2.5 p-3.5 rounded-DEFAULT bg-tertiary-container/40 border border-tertiary/30">
    <span class="font-label-sm text-label-sm text-on-surface uppercase font-bold flex items-center gap-1.5">
      <span class="material-symbols-outlined text-[16px]">verified</span>
      Статус (модератор)
    </span>
    <div class="flex flex-wrap gap-2">
      <button
        v-for="step in STEPS"
        :key="step.id"
        type="button"
        class="px-3 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all flex items-center gap-1.5"
        :class="
          point.status === step.id
            ? 'bg-secondary text-on-secondary'
            : 'bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container'
        "
        :disabled="pending !== null"
        @click="setStatus(step.id)"
      >
        <span v-if="pending === step.id" class="material-symbols-outlined text-[14px] animate-spin">sync</span>
        {{ step.label }}
      </button>
    </div>
    <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>
  </div>
</template>
