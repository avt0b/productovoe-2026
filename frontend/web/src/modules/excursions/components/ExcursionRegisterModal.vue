<script setup>
import { reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as excursionsApi from '../api.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  excursion: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'registered'])

const { session } = useAuthSession()

const MODES = [
  { id: 'individual', label: 'Я один(на)', icon: 'person' },
  { id: 'group', label: 'Группа — школа, клуб', icon: 'groups_3' },
]

const form = reactive({ mode: 'individual', org: '', groupSize: '' })
const status = ref('idle') // idle | sending | done
const error = ref('')

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    form.mode = 'individual'
    form.org = ''
    form.groupSize = ''
    status.value = 'idle'
    error.value = ''
  },
)

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  error.value = ''
  if (session.status !== 'authenticated') {
    error.value = 'Войдите, чтобы записаться на экскурсию'
    return
  }
  if (form.mode === 'group' && !form.org.trim()) {
    error.value = 'Укажите название школы или клуба'
    return
  }
  status.value = 'sending'
  try {
    await excursionsApi.registerForExcursion(session.accessToken, props.excursion.id, {
      organizationName: form.mode === 'group' ? form.org.trim() : '',
      groupSize: form.mode === 'group' ? (form.groupSize ? Number(form.groupSize) : 1) : 1,
    })
    status.value = 'done'
    emit('registered')
    setTimeout(close, 1200)
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось отправить заявку'
  }
}
</script>

<template>
  <div
    v-if="modelValue && excursion"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-md w-full shadow-2xl flex flex-col overflow-hidden">
      <div class="flex items-center justify-between p-5 border-b border-surface-container-high">
        <div class="flex flex-col min-w-0">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold truncate">Запись на экскурсию</span>
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
        <div class="flex flex-wrap gap-2">
          <button
            v-for="opt in MODES"
            :key="opt.id"
            type="button"
            class="px-3.5 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all flex items-center gap-1.5"
            :class="
              form.mode === opt.id
                ? 'bg-secondary text-on-secondary'
                : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
            "
            @click="form.mode = opt.id"
          >
            <span class="material-symbols-outlined text-[16px]">{{ opt.icon }}</span>
            {{ opt.label }}
          </button>
        </div>

        <template v-if="form.mode === 'group'">
          <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
              Школа или клуб
            </label>
            <input
              v-model="form.org"
              type="text"
              placeholder="Например, школа № 12, г. Орёл"
              class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
            />
          </div>
          <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
              Размер группы
            </label>
            <input
              v-model="form.groupSize"
              type="number"
              min="1"
              placeholder="15"
              class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
            />
          </div>
        </template>

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

        <button
          type="submit"
          class="mt-1 px-5 py-2.5 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2"
          :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
          :disabled="status === 'sending'"
        >
          <span class="material-symbols-outlined text-[18px]">
            {{ status === 'done' ? 'check_circle' : status === 'sending' ? 'sync' : 'send' }}
          </span>
          <span>{{ status === 'done' ? 'Заявка отправлена' : status === 'sending' ? 'Отправляем...' : 'Отправить заявку' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>
