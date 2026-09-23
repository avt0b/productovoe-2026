<script setup>
import { reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as excursionsApi from '../api.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  excursion: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'rated'])

const { session } = useAuthSession()

const form = reactive({ rating: 5, comment: '' })
const status = ref('idle') // idle | sending | done
const error = ref('')

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    form.rating = 5
    form.comment = ''
    status.value = 'idle'
    error.value = ''
  },
)

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  error.value = ''
  status.value = 'sending'
  try {
    await excursionsApi.rateExcursion(session.accessToken, props.excursion.id, {
      rating: form.rating,
      comment: form.comment.trim(),
    })
    status.value = 'done'
    emit('rated')
    setTimeout(close, 1000)
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось отправить оценку'
  }
}
</script>

<template>
  <div
    v-if="modelValue && excursion"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-sm w-full shadow-2xl flex flex-col overflow-hidden">
      <div class="flex items-center justify-between p-5 border-b border-surface-container-high">
        <div class="flex flex-col min-w-0">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold">Оценить гида</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant truncate">{{ excursion.title }}</span>
        </div>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors shrink-0"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <form class="p-5 flex flex-col gap-3" @submit.prevent="submit">
        <div class="flex items-center justify-center gap-1">
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            class="material-symbols-outlined text-[36px] transition-colors"
            :class="n <= form.rating ? 'text-tertiary' : 'text-outline-variant hover:text-tertiary/60'"
            :style="n <= form.rating ? { fontVariationSettings: `'FILL' 1` } : {}"
            @click="form.rating = n"
          >
            star
          </button>
        </div>
        <textarea
          v-model="form.comment"
          rows="3"
          placeholder="Что понравилось, что можно улучшить (необязательно)"
          class="w-full px-3.5 py-2.5 rounded-DEFAULT bg-surface-container-low font-body-sm text-body-sm text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
        />

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

        <button
          type="submit"
          class="px-5 py-2.5 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2"
          :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
          :disabled="status === 'sending'"
        >
          <span class="material-symbols-outlined text-[18px]">
            {{ status === 'done' ? 'check_circle' : status === 'sending' ? 'sync' : 'send' }}
          </span>
          <span>{{ status === 'done' ? 'Спасибо за оценку' : status === 'sending' ? 'Отправляем...' : 'Отправить оценку' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>
