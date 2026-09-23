<script setup>
import { computed, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import { useProfileStore } from '../profileStore.js'
import { uploadVerificationDocument } from '../api.js'

const { session } = useAuthSession()
const { profile } = useProfileStore()

// На бэке (user_service) есть только флаг Profile.is_verified и ручка
// PATCH /profiles/{id}/verify, которую может дёрнуть только уже
// верифицированный краевед/наставник/модератор — своей заявки с документами
// там нет вообще (нет ни модели, ни очереди на проверку). Поэтому заявка —
// честный фронтовый черновик: файл реально загружается в media_service
// (единственная существующая ручка загрузки, только картинки), а сам факт
// «заявка подана» и ссылки на документы хранятся только в этом браузере —
// это ДЕМО-очередь, а не настоящая модерация.
function storageKey(profileId) {
  return `marshruty.local-historian-verification.${profileId}`
}

function loadSubmission(profileId) {
  try {
    const raw = localStorage.getItem(storageKey(profileId))
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const submission = ref(null)
watch(
  () => profile.data?.id,
  (id) => {
    submission.value = id ? loadSubmission(id) : null
  },
  { immediate: true },
)

const isLocalHistorian = computed(() => profile.data?.role === 'local_historian')

const file = ref(null)
const docType = ref('membership')
const note = ref('')
const status = ref('idle') // idle | uploading | error
const error = ref('')

function onFileChange(event) {
  file.value = event.target.files?.[0] ?? null
}

async function submit() {
  if (!file.value) {
    error.value = 'Приложите фото документа'
    return
  }
  error.value = ''
  status.value = 'uploading'
  try {
    const { url } = await uploadVerificationDocument(session.accessToken, file.value)
    const record = {
      documentUrl: url,
      docType: docType.value,
      note: note.value.trim(),
      submittedAt: new Date().toISOString(),
    }
    localStorage.setItem(storageKey(profile.data.id), JSON.stringify(record))
    submission.value = record
    file.value = null
    note.value = ''
    status.value = 'idle'
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось загрузить документ'
  }
}

function withdraw() {
  localStorage.removeItem(storageKey(profile.data.id))
  submission.value = null
}

const DOC_TYPE_LABELS = {
  membership: 'Членский билет краеведческого общества',
  diploma: 'Диплом/документ об образовании',
  other: 'Другой подтверждающий документ',
}
</script>

<template>
  <div
    v-if="session.status === 'authenticated' && isLocalHistorian"
    class="bg-surface-container-lowest p-6 rounded-DEFAULT shadow-sm flex flex-col"
  >
    <div class="flex items-center gap-3 mb-2">
      <div class="w-10 h-10 rounded-full bg-surface-container-high text-on-surface flex items-center justify-center">
        <span class="material-symbols-outlined text-[20px]">verified</span>
      </div>
      <div class="flex flex-col">
        <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Подтверждение статуса краеведа</h2>
        <span class="font-body-sm text-body-sm text-on-surface-variant">user_service, Profile.is_verified</span>
      </div>
    </div>

    <div v-if="profile.data?.is_verified" class="flex items-center gap-2 bg-secondary-container text-on-secondary-container px-4 py-3 rounded-DEFAULT">
      <span class="material-symbols-outlined text-[20px]">check_circle</span>
      <span class="font-body-sm text-body-sm font-bold">Статус краеведа подтверждён модератором</span>
    </div>

    <template v-else>
      <p class="font-body-sm text-body-sm text-on-surface-variant mb-3">
        Приложите фото документа (членский билет краеведческого общества или диплом/документ об образовании) —
        это станет основанием, чтобы модератор подтвердил ваш статус.
        <span class="font-bold">
          Демо: очереди модерации документов на бэкенде пока нет, заявка сохраняется только в этом браузере.
        </span>
      </p>

      <div v-if="submission" class="flex flex-col gap-3">
        <div class="flex items-center gap-3 bg-tertiary-fixed text-on-tertiary-fixed px-4 py-3 rounded-DEFAULT">
          <span class="material-symbols-outlined text-[20px]">hourglass_top</span>
          <div class="flex flex-col min-w-0">
            <span class="font-body-sm text-body-sm font-bold">Заявка отправлена, ожидает проверки (демо)</span>
            <span class="font-label-sm text-label-sm opacity-80">
              {{ DOC_TYPE_LABELS[submission.docType] ?? submission.docType }} ·
              {{ new Date(submission.submittedAt).toLocaleString('ru-RU') }}
            </span>
          </div>
        </div>
        <a :href="submission.documentUrl" target="_blank" rel="noopener" class="block">
          <img :src="submission.documentUrl" alt="Загруженный документ" class="max-h-40 rounded-DEFAULT object-cover" />
        </a>
        <p v-if="submission.note" class="font-body-sm text-body-sm text-on-surface-variant">{{ submission.note }}</p>
        <button
          type="button"
          class="self-start px-4 py-2 rounded-full bg-surface-container text-on-surface font-label-sm text-label-sm font-bold hover:bg-surface-container-high transition-colors"
          @click="withdraw"
        >
          Отозвать заявку
        </button>
      </div>

      <form v-else class="flex flex-col gap-3" @submit.prevent="submit">
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Тип документа</label>
          <select
            v-model="docType"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          >
            <option value="membership">Членский билет краеведческого общества</option>
            <option value="diploma">Диплом/документ об образовании</option>
            <option value="other">Другой документ</option>
          </select>
        </div>

        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Фото документа</label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="w-full font-body-sm text-body-sm text-on-surface-variant file:mr-3 file:px-4 file:py-2 file:rounded-full file:border-0 file:bg-primary file:text-on-primary file:font-label-sm file:text-label-sm file:font-bold"
            @change="onFileChange"
          />
        </div>

        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Комментарий (необязательно)</label>
          <textarea
            v-model="note"
            rows="2"
            placeholder="Например: номер и дата выдачи документа"
            class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
          />
        </div>

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

        <button
          type="submit"
          class="self-end px-6 py-2.5 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm flex items-center gap-2 disabled:opacity-60"
          :disabled="status === 'uploading'"
        >
          <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': status === 'uploading' }">
            {{ status === 'uploading' ? 'sync' : 'upload' }}
          </span>
          <span>{{ status === 'uploading' ? 'Загружаем...' : 'Отправить на проверку' }}</span>
        </button>
      </form>
    </template>
  </div>
</template>
