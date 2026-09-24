<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
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

// media_render_worker реально разбирает очередь (claim -> SpeechKit ->
// Replicate/SadTalker -> MinIO -> ready/failed), но опрашивает media_service
// сам по себе — здесь никто не узнает о готовности, пока не перечитает
// список. Пока есть заявки в queued/processing, тихо обновляем список раз в
// 4 секунды; как только все разошлись по ready/failed — опрос сам стихает.
let pollTimer = null

function hasPending() {
  return myClips.value.some((c) => c.status === 'queued' || c.status === 'processing')
}

async function pollIfNeeded() {
  if (!hasPending()) return
  try {
    myClips.value = await api.listMyClips(session.accessToken)
  } catch {
    // сбой опроса — не страшно, следующий тик попробует снова
  }
}

onMounted(async () => {
  await loadMine()
  pollTimer = setInterval(pollIfNeeded, 4000)
})
onUnmounted(() => clearInterval(pollTimer))

const form = reactive({
  soldierName: '',
  sourcePhotoUrl: '',
  narrationText: 'Я сделал это, чтобы ты жил и видел голубое небо. Помни меня.',
  voiceStyle: 'era_male',
  isPublic: false,
  consent: false,
})
const submitStatus = ref('idle') // idle | uploading | pending | done
const error = ref('')
const photoFile = ref(null)

const canSubmit = computed(() => session.status === 'authenticated')

const previewUrl = ref('')

function onPhotoChange(event) {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  photoFile.value = event.target.files?.[0] ?? null
  previewUrl.value = photoFile.value ? URL.createObjectURL(photoFile.value) : ''
  form.sourcePhotoUrl = ''
}
onUnmounted(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})

async function submit() {
  if (!canSubmit.value) {
    error.value = 'Войдите, чтобы отправить заявку'
    return
  }
  if (!photoFile.value && !form.sourcePhotoUrl) {
    error.value = 'Приложите фотографию бойца'
    return
  }
  if (!form.consent) {
    error.value = 'Подтвердите согласие на мемориальное использование'
    return
  }
  error.value = ''
  try {
    let photoUrl = form.sourcePhotoUrl
    if (photoFile.value) {
      submitStatus.value = 'uploading'
      const { url } = await api.uploadSourcePhoto(session.accessToken, photoFile.value)
      photoUrl = url
    }
    submitStatus.value = 'pending'
    const clip = await api.createClip(session.accessToken, {
      soldier_name: form.soldierName,
      source_photo_url: photoUrl,
      narration_text: form.narrationText,
      voice_style: form.voiceStyle,
      is_public: form.isPublic,
      consent_memorial_use: form.consent,
    })
    myClips.value.unshift(clip)
    submitStatus.value = 'done'
    if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
    photoFile.value = null
    previewUrl.value = ''
    form.sourcePhotoUrl = ''
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
          media_render_worker реально разбирает очередь: озвучивает текст через Yandex SpeechKit и
          анимирует фото под голос через Replicate (SadTalker). Без настроенных ключей на этом
          стенде шаг генерации честно завершится ошибкой — заявку можно будет отправить в очередь
          заново кнопкой «Повторить»
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
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Фотография бойца
          </label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="w-full font-body-sm text-body-sm text-on-surface-variant file:mr-3 file:px-4 file:py-2 file:rounded-full file:border-0 file:bg-primary file:text-on-primary file:font-label-sm file:text-label-sm file:font-bold"
            @change="onPhotoChange"
          />
        </div>
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
          class="h-11 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2 self-start px-6 disabled:opacity-60"
          :class="submitStatus === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
          :disabled="submitStatus === 'uploading' || submitStatus === 'pending'"
        >
          <span
            class="material-symbols-outlined text-[18px]"
            :class="{ 'animate-spin': submitStatus === 'uploading' || submitStatus === 'pending' }"
          >
            {{
              submitStatus === 'done'
                ? 'check_circle'
                : submitStatus === 'uploading' || submitStatus === 'pending'
                  ? 'sync'
                  : 'send'
            }}
          </span>
          <span>
            {{
              submitStatus === 'done'
                ? 'Заявка отправлена'
                : submitStatus === 'uploading'
                  ? 'Загружаем фото...'
                  : submitStatus === 'pending'
                    ? 'Отправляем...'
                    : 'Отправить заявку'
            }}
          </span>
        </button>
      </div>

      <div class="w-full aspect-[4/3] rounded-DEFAULT overflow-hidden bg-surface-container-high">
        <SmartImage :src="previewUrl" icon="portrait" />
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

        <video
          v-if="clip.status === 'ready' && clip.video_url"
          :src="clip.video_url"
          controls
          class="w-full max-h-72 bg-ink"
        />

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
