<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import SmartImage from '@shared/components/SmartImage.vue'
import { useAuthSession } from '@modules/auth'
import * as api from '../api.js'

const { session } = useAuthSession()

const VOICE_OPTIONS = [
  { id: 'era_male', label: 'Мужской голос эпохи' },
  { id: 'era_female', label: 'Женский голос эпохи' },
  { id: 'neutral', label: 'Нейтральный' },
]

const STATUS_META = {
  queued: { label: 'В очереди', class: 'bg-surface-container-high text-on-surface-variant', icon: 'schedule' },
  processing: { label: 'Генерируется', class: 'bg-tertiary-fixed text-on-tertiary-fixed', icon: 'sync' },
  ready: { label: 'Готово', class: 'bg-secondary-fixed text-on-secondary-fixed', icon: 'check_circle' },
  failed: { label: 'Ошибка генерации', class: 'bg-error-container text-on-error-container', icon: 'error' },
}

const myClips = ref([])
const loadStatus = ref('idle')

async function loadMine() {
  if (session.status !== 'authenticated') return
  loadStatus.value = 'loading'
  try {
    myClips.value = await api.listMyClips(session.accessToken)
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

onMounted(loadMine)

const form = reactive({
  soldierName: '',
  sourcePhotoUrl: '',
  narrationText: 'Я сделал это, чтобы ты жил и видел голубое небо. Помни меня.',
  voiceStyle: 'era_male',
  isPublic: false,
  consent: false,
})
const submitStatus = ref('idle')
const error = ref('')

const canSubmit = computed(() => session.status === 'authenticated')

async function submit() {
  if (!canSubmit.value) {
    error.value = 'Войдите, чтобы отправить заявку'
    return
  }
  if (!form.sourcePhotoUrl) {
    error.value = 'Укажите ссылку на фотографию бойца'
    return
  }
  if (!form.consent) {
    error.value = 'Подтвердите согласие на мемориальное использование'
    return
  }
  submitStatus.value = 'pending'
  error.value = ''
  try {
    const clip = await api.createClip(session.accessToken, {
      soldier_name: form.soldierName,
      source_photo_url: form.sourcePhotoUrl,
      narration_text: form.narrationText,
      voice_style: form.voiceStyle,
      is_public: form.isPublic,
      consent_memorial_use: form.consent,
    })
    myClips.value.unshift(clip)
    submitStatus.value = 'done'
    setTimeout(() => (submitStatus.value = 'idle'), 1200)
  } catch (err) {
    submitStatus.value = 'idle'
    error.value = err.detail ?? 'Не удалось отправить заявку'
  }
}

const retryError = ref('')

async function retry(clip) {
  retryError.value = ''
  try {
    const updated = await api.retryClip(session.accessToken, clip.id)
    const i = myClips.value.findIndex((c) => c.id === clip.id)
    if (i !== -1) myClips.value[i] = updated
  } catch (err) {
    retryError.value = err.detail ?? 'Не удалось поставить заявку в очередь заново'
  }
}

const shareOpenId = ref(null)
const shareForm = reactive({ recipient: '', note: '' })
const shareStatus = ref('idle') // idle | sending | done
const shareError = ref('')

function openShare(clip) {
  shareOpenId.value = shareOpenId.value === clip.id ? null : clip.id
  shareForm.recipient = ''
  shareForm.note = ''
  shareStatus.value = 'idle'
  shareError.value = ''
}

async function sendShare(clip) {
  shareError.value = ''
  if (!shareForm.recipient.trim()) {
    shareError.value = 'Укажите, кому отправить — e-mail, телефон или соцсеть'
    return
  }
  shareStatus.value = 'sending'
  try {
    await api.shareClip(session.accessToken, clip.id, { recipient: shareForm.recipient.trim(), note: shareForm.note.trim() })
    shareStatus.value = 'done'
    setTimeout(() => (shareOpenId.value = null), 1500)
  } catch (err) {
    shareStatus.value = 'idle'
    shareError.value = err.detail ?? 'Не удалось отправить'
  }
}
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-5">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-primary text-[22px]">smart_toy</span>
      <div class="flex flex-col">
        <span class="font-headline-sm text-headline-sm text-on-surface">Своё «живое фото»</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Заявка уходит в media_service — реальную AI-генерацию выполняет внешний воркер, которого
          в этом окружении нет, поэтому статус останется «В очереди»
        </span>
      </div>
    </div>

    <form class="grid grid-cols-1 md:grid-cols-2 gap-4" @submit.prevent="submit">
      <div class="flex flex-col gap-3">
        <input
          v-model="form.soldierName"
          type="text"
          placeholder="Имя бойца (если известно)"
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
        <input
          v-model="form.sourcePhotoUrl"
          type="text"
          placeholder="Ссылка на фотографию бойца"
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
        <textarea
          v-model="form.narrationText"
          rows="3"
          class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
        />
        <div class="flex flex-wrap gap-2">
          <button
            v-for="opt in VOICE_OPTIONS"
            :key="opt.id"
            type="button"
            class="px-3 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all"
            :class="
              form.voiceStyle === opt.id
                ? 'bg-secondary text-on-secondary'
                : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
            "
            @click="form.voiceStyle = opt.id"
          >
            {{ opt.label }}
          </button>
        </div>
        <label class="flex items-start gap-2 cursor-pointer select-none">
          <input v-model="form.consent" type="checkbox" class="w-4 h-4 mt-0.5 rounded accent-primary cursor-pointer" />
          <span class="font-body-sm text-body-sm text-on-surface-variant">
            Технология применяется только в мемориальных целях, с уважением к памяти — подтверждаю
          </span>
        </label>
        <label class="flex items-center gap-2 cursor-pointer select-none">
          <input v-model="form.isPublic" type="checkbox" class="w-4 h-4 rounded accent-primary cursor-pointer" />
          <span class="font-body-sm text-body-sm text-on-surface-variant">Показать в общем мемориале платформы</span>
        </label>

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

        <button
          type="submit"
          class="h-11 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2 self-start px-6"
          :class="submitStatus === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
          :disabled="submitStatus === 'pending'"
        >
          <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': submitStatus === 'pending' }">
            {{ submitStatus === 'done' ? 'check_circle' : submitStatus === 'pending' ? 'sync' : 'send' }}
          </span>
          <span>{{ submitStatus === 'done' ? 'Заявка отправлена' : 'Отправить заявку' }}</span>
        </button>
      </div>

      <div class="w-full aspect-[4/3] rounded-DEFAULT overflow-hidden bg-surface-container-high">
        <SmartImage :src="form.sourcePhotoUrl" icon="portrait" />
      </div>
    </form>

    <div v-if="session.status === 'authenticated'" class="flex flex-col gap-2.5 pt-2 border-t border-surface-container-high">
      <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold pt-3">Мои заявки</span>
      <p v-if="loadStatus === 'loaded' && !myClips.length" class="font-body-sm text-body-sm text-on-surface-variant">
        Заявок пока нет.
      </p>
      <p v-if="retryError" class="font-label-sm text-label-sm text-error font-bold">{{ retryError }}</p>
      <div v-for="clip in myClips" :key="clip.id" class="bg-surface-container-low rounded-DEFAULT overflow-hidden">
        <div class="p-3.5 flex items-center justify-between gap-3">
          <div class="flex flex-col min-w-0">
            <span class="font-label-md text-label-md text-on-surface font-bold truncate">
              {{ clip.soldier_name || 'Без имени' }}
            </span>
            <span v-if="clip.status === 'failed' && clip.error" class="font-body-sm text-body-sm text-error truncate">
              {{ clip.error }}
            </span>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <span
              class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-bold flex items-center gap-1"
              :class="STATUS_META[clip.status].class"
            >
              <span class="material-symbols-outlined text-[14px]">{{ STATUS_META[clip.status].icon }}</span>
              {{ STATUS_META[clip.status].label }}
            </span>
            <button
              v-if="clip.status === 'failed'"
              class="px-3 py-1 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm font-bold"
              @click="retry(clip)"
            >
              Повторить
            </button>
            <button
              v-if="clip.status === 'ready'"
              class="px-3 py-1 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm font-bold flex items-center gap-1"
              @click="openShare(clip)"
            >
              <span class="material-symbols-outlined text-[16px]">forward</span>
              Отправить родным
            </button>
          </div>
        </div>

        <div v-if="shareOpenId === clip.id" class="p-3.5 pt-0 flex flex-col gap-2">
          <input
            v-model="shareForm.recipient"
            type="text"
            placeholder="E-mail, телефон или профиль родных"
            class="w-full h-10 px-3.5 rounded-full bg-surface-container font-body-sm text-body-sm text-on-surface outline-none focus:bg-surface-container-high transition-colors"
          />
          <input
            v-model="shareForm.note"
            type="text"
            placeholder="Сопроводительная записка (необязательно)"
            class="w-full h-10 px-3.5 rounded-full bg-surface-container font-body-sm text-body-sm text-on-surface outline-none focus:bg-surface-container-high transition-colors"
          />
          <p v-if="shareError" class="font-label-sm text-label-sm text-error font-bold">{{ shareError }}</p>
          <button
            type="button"
            class="self-start px-4 py-1.5 rounded-full font-label-sm text-label-sm font-bold flex items-center gap-1.5"
            :class="shareStatus === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
            :disabled="shareStatus === 'sending'"
            @click="sendShare(clip)"
          >
            <span class="material-symbols-outlined text-[16px]">{{ shareStatus === 'done' ? 'check_circle' : 'send' }}</span>
            {{ shareStatus === 'done' ? 'Отправлено' : 'Отправить' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
