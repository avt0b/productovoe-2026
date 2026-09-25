<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as archiveApi from '../api.js'

const { session } = useAuthSession()

// Кто может модерировать — так же решает и бэкенд.
const VERIFIER_ROLES = new Set(['searcher', 'local_historian', 'mentor', 'moderator'])
const canVerify = computed(
  () => session.status === 'authenticated' && (session.user?.is_root || VERIFIER_ROLES.has(session.user?.role)),
)

const KIND_OPTIONS = [
  { id: 'event', label: 'Локальное событие', icon: 'flag' },
  { id: 'memory', label: 'Воспоминание очевидца', icon: 'record_voice_over' },
  { id: 'soldier_card', label: 'Карточка бойца', icon: 'badge' },
  { id: 'photo_story', label: 'Фото + история', icon: 'photo_camera' },
]
const KIND_META = Object.fromEntries(KIND_OPTIONS.map((k) => [k.id, k]))

const statusMeta = {
  verified: { label: 'Подтверждено', class: 'bg-secondary-fixed text-on-secondary-fixed', icon: 'verified' },
  pending: { label: 'На проверке', class: 'bg-tertiary-fixed text-on-tertiary-fixed', icon: 'hourglass_top' },
  rejected: { label: 'Отклонено', class: 'bg-error-container text-on-error-container', icon: 'cancel' },
}

// --- лента ---
const publicEntries = ref([])
const myEntries = ref([])
const loadStatus = ref('idle')

async function loadFeed() {
  loadStatus.value = 'loading'
  try {
    const requests = [archiveApi.listVerifiedEntries()]
    if (session.status === 'authenticated') requests.push(archiveApi.listMyEntries(session.accessToken))
    const [verified, mine] = await Promise.all(requests)
    publicEntries.value = Array.isArray(verified) ? verified : []
    myEntries.value = Array.isArray(mine) ? mine : []
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

const feed = computed(() => {
  const seen = new Set(myEntries.value.map((e) => e.id))
  return [...myEntries.value, ...publicEntries.value.filter((e) => !seen.has(e.id))].sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at),
  )
})

// Имена авторов — одним батч-запросом на все id, что сейчас на экране
// (GET /profiles/batch публична, токен не нужен, до 200 id за раз).
const authorsById = ref({})

async function resolveAuthors(entries) {
  const ids = entries.map((e) => e.submitted_by).filter((id) => id && !(id in authorsById.value))
  if (!ids.length) return
  try {
    const profiles = await archiveApi.getAuthorsBatch(ids)
    const patch = Object.fromEntries((Array.isArray(profiles) ? profiles : []).map((p) => [p.id, p]))
    authorsById.value = { ...authorsById.value, ...patch }
  } catch {
    // Лента и без имён останется читаемой — просто откатимся к заглушке.
  }
}

watch(feed, (entries) => resolveAuthors(entries))

function authorLabel(entry) {
  if (entry.submitted_by === session.user?.id) return 'Вы'
  return authorsById.value[entry.submitted_by]?.display_name ?? 'Участник платформы'
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
}

// --- очередь модерации (только для верификаторов) ---
const activeTab = ref('feed') // feed | moderation
const moderationEntries = ref([])
const moderationStatus = ref('idle')

async function loadModeration() {
  if (!canVerify.value) return
  moderationStatus.value = 'loading'
  try {
    const rows = await archiveApi.listModerationEntries(session.accessToken, 'pending')
    moderationEntries.value = Array.isArray(rows) ? rows : []
    moderationStatus.value = 'loaded'
  } catch {
    moderationStatus.value = 'error'
  }
}

watch(activeTab, (tab) => {
  if (tab === 'moderation' && moderationStatus.value === 'idle') loadModeration()
})
watch(moderationEntries, (entries) => resolveAuthors(entries))

const reviewingId = ref(null)
const reviewError = ref('')

async function review(entry, action) {
  reviewingId.value = entry.id
  reviewError.value = ''
  try {
    const call = action === 'verify' ? archiveApi.verifyEntry : archiveApi.rejectEntry
    await call(session.accessToken, entry.id)
    moderationEntries.value = moderationEntries.value.filter((e) => e.id !== entry.id)
    if (session.status === 'authenticated') myEntries.value = await archiveApi.listMyEntries(session.accessToken)
  } catch (err) {
    reviewError.value = err.detail ?? 'Не удалось отправить решение'
  } finally {
    reviewingId.value = null
  }
}

onMounted(loadFeed)

// --- форма публикации ---
const formOpen = ref(false)
const form = reactive({ kind: 'event', title: '', body: '', dateText: '' })
const photoFile = ref(null)
const audioFile = ref(null)
const submitStatus = ref('idle') // idle | uploading | pending | done
const error = ref('')

function onPhotoChange(event) {
  photoFile.value = event.target.files?.[0] ?? null
}

function onAudioChange(event) {
  audioFile.value = event.target.files?.[0] ?? null
}

async function submit() {
  if (session.status !== 'authenticated') {
    error.value = 'Войдите, чтобы предложить событие'
    return
  }
  if (!form.title.trim()) {
    error.value = 'Укажите название'
    return
  }
  error.value = ''
  try {
    let mediaUrl
    let audioUrl
    if (photoFile.value) {
      submitStatus.value = 'uploading'
      const { url } = await archiveApi.uploadEntryPhoto(session.accessToken, photoFile.value)
      mediaUrl = url
    }
    if (audioFile.value) {
      submitStatus.value = 'uploading'
      const { url } = await archiveApi.uploadEntryAudio(session.accessToken, audioFile.value)
      audioUrl = url
    }
    submitStatus.value = 'pending'
    const entry = await archiveApi.createEntry(session.accessToken, {
      kind: form.kind,
      title: form.title.trim(),
      body: form.body.trim(),
      date_text: form.dateText.trim(),
      ...(mediaUrl ? { media_url: mediaUrl } : {}),
      ...(audioUrl ? { audio_url: audioUrl } : {}),
    })
    myEntries.value.unshift(entry)
    submitStatus.value = 'done'
    form.title = ''
    form.body = ''
    form.dateText = ''
    photoFile.value = null
    audioFile.value = null
    setTimeout(() => {
      formOpen.value = false
      submitStatus.value = 'idle'
    }, 1200)
  } catch (err) {
    submitStatus.value = 'idle'
    error.value = err.detail ?? 'Не удалось отправить событие'
  }
}
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="flex items-center gap-2 bg-surface-container-lowest rounded-full p-1 self-start shadow-sm">
      <button
        type="button"
        class="px-4 py-2 rounded-full font-label-md text-label-md font-bold transition-colors"
        :class="activeTab === 'feed' ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container-high'"
        @click="activeTab = 'feed'"
      >
        Лента
      </button>
      <button
        v-if="canVerify"
        type="button"
        class="px-4 py-2 rounded-full font-label-md text-label-md font-bold transition-colors flex items-center gap-1.5"
        :class="
          activeTab === 'moderation' ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container-high'
        "
        @click="activeTab = 'moderation'"
      >
        На проверке
        <span
          v-if="moderationEntries.length"
          class="px-1.5 py-0.5 rounded-full text-[11px] font-bold"
          :class="activeTab === 'moderation' ? 'bg-on-primary/20' : 'bg-tertiary-fixed text-on-tertiary-fixed'"
        >
          {{ moderationEntries.length }}
        </span>
      </button>
    </div>

    <template v-if="activeTab === 'feed'">
      <div class="bg-surface-container-lowest rounded-2xl shadow-document overflow-hidden">
        <button
          type="button"
          class="w-full text-left p-4 flex items-center gap-3 text-on-surface-variant hover:bg-surface-container-low transition-colors"
          @click="formOpen = !formOpen"
        >
          <span class="material-symbols-outlined text-[20px]">edit_note</span>
          <span class="font-body-md text-body-md flex-1">Предложить событие, воспоминание или карточку бойца...</span>
          <span class="material-symbols-outlined text-[20px]" :class="{ 'rotate-180': formOpen }">expand_more</span>
        </button>

        <form v-if="formOpen" class="p-4 pt-0 flex flex-col gap-3 border-t border-surface-container-high" @submit.prevent="submit">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="opt in KIND_OPTIONS"
              :key="opt.id"
              type="button"
              class="px-3 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all flex items-center gap-1.5"
              :class="
                form.kind === opt.id
                  ? 'bg-secondary text-on-secondary'
                  : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
              "
              @click="form.kind = opt.id"
            >
              <span class="material-symbols-outlined text-[16px]">{{ opt.icon }}</span>
              {{ opt.label }}
            </button>
          </div>
          <input
            v-model="form.title"
            type="text"
            placeholder="Название события, объекта или имя бойца"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
          <textarea
            v-model="form.body"
            rows="3"
            placeholder="Что произошло, кто рассказал, есть ли документы — расскажите подробно"
            class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
          />
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input
              v-model="form.dateText"
              type="text"
              placeholder="Дата (если известна): напр. «октябрь 1941»"
              class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
            />
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="w-full font-body-sm text-body-sm text-on-surface-variant file:mr-3 file:px-4 file:py-2 file:rounded-full file:border-0 file:bg-secondary file:text-on-secondary file:font-label-sm file:text-label-sm file:font-bold"
              @change="onPhotoChange"
            />
            <input
              type="file"
              accept="audio/mpeg,audio/ogg,audio/wav,audio/mp4,audio/x-m4a,audio/webm"
              class="w-full font-body-sm text-body-sm text-on-surface-variant file:mr-3 file:px-4 file:py-2 file:rounded-full file:border-0 file:bg-secondary file:text-on-secondary file:font-label-sm file:text-label-sm file:font-bold"
              @change="onAudioChange"
            />
          </div>
          <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>
          <button
            type="submit"
            class="self-end px-5 py-2 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm flex items-center gap-2 disabled:opacity-60"
            :disabled="submitStatus === 'uploading' || submitStatus === 'pending'"
          >
            <span
              v-if="submitStatus === 'uploading' || submitStatus === 'pending'"
              class="material-symbols-outlined text-[18px] animate-spin"
            >
              sync
            </span>
            <span>
              {{
                submitStatus === 'uploading'
                  ? 'Загружаем фото...'
                  : submitStatus === 'pending'
                    ? 'Публикуем...'
                    : submitStatus === 'done'
                      ? 'Отправлено на проверку'
                      : 'Опубликовать'
              }}
            </span>
          </button>
        </form>
      </div>

      <p v-if="loadStatus === 'loaded' && !feed.length" class="font-body-md text-body-md text-on-surface-variant text-center py-8">
        Записей пока нет — станьте первым, кто предложит событие.
      </p>
      <p v-if="loadStatus === 'error'" class="font-body-sm text-body-sm text-error text-center py-8">
        Не удалось загрузить ленту — попробуйте позже
      </p>

      <div v-for="entry in feed" :key="entry.id" class="bg-surface-container-lowest rounded-2xl shadow-document p-4 flex flex-col gap-3">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-10 h-10 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center shrink-0">
              <span class="material-symbols-outlined text-[20px]">{{ KIND_META[entry.kind]?.icon ?? 'history_edu' }}</span>
            </div>
            <div class="flex flex-col min-w-0">
              <span class="font-label-md text-label-md text-on-surface font-bold">{{ authorLabel(entry) }}</span>
              <span class="font-label-sm text-label-sm text-on-surface-variant">
                {{ KIND_META[entry.kind]?.label ?? entry.kind }} · {{ formatDate(entry.created_at) }}
              </span>
            </div>
          </div>
          <span
            class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-bold flex items-center gap-1 shrink-0"
            :class="statusMeta[entry.status]?.class"
          >
            <span class="material-symbols-outlined text-[14px]">{{ statusMeta[entry.status]?.icon }}</span>
            {{ statusMeta[entry.status]?.label ?? entry.status }}
          </span>
        </div>

        <div class="flex flex-col gap-1">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold">{{ entry.title }}</span>
          <span v-if="entry.date_text" class="font-label-sm text-label-sm text-tertiary font-bold">{{ entry.date_text }}</span>
          <p v-if="entry.body" class="font-body-md text-body-md text-on-surface [overflow-wrap:anywhere]">{{ entry.body }}</p>
        </div>

        <img v-if="entry.media_url" :src="entry.media_url" alt="" class="max-h-72 w-full object-cover rounded-DEFAULT" />
        <audio v-if="entry.audio_url" :src="entry.audio_url" controls class="w-full" />
      </div>
    </template>

    <template v-else>
      <p v-if="moderationStatus === 'loading'" class="font-body-md text-body-md text-on-surface-variant text-center py-8">
        Загружаем очередь...
      </p>
      <p
        v-else-if="moderationStatus === 'loaded' && !moderationEntries.length"
        class="font-body-md text-body-md text-on-surface-variant text-center py-8"
      >
        Очередь пуста — новых заявок на проверку нет.
      </p>
      <p v-if="reviewError" class="font-label-sm text-label-sm text-error font-bold">{{ reviewError }}</p>

      <div
        v-for="entry in moderationEntries"
        :key="entry.id"
        class="bg-surface-container-lowest rounded-2xl shadow-document p-4 flex flex-col gap-3"
      >
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[18px] text-tertiary">{{ KIND_META[entry.kind]?.icon ?? 'history_edu' }}</span>
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">
            {{ KIND_META[entry.kind]?.label ?? entry.kind }} · {{ formatDate(entry.created_at) }}
          </span>
        </div>
        <span class="font-headline-sm text-headline-sm text-on-surface font-bold">{{ entry.title }}</span>
        <span v-if="entry.date_text" class="font-label-sm text-label-sm text-tertiary font-bold">{{ entry.date_text }}</span>
        <p v-if="entry.body" class="font-body-md text-body-md text-on-surface [overflow-wrap:anywhere]">{{ entry.body }}</p>
        <img v-if="entry.media_url" :src="entry.media_url" alt="" class="max-h-72 w-full object-cover rounded-DEFAULT" />
        <audio v-if="entry.audio_url" :src="entry.audio_url" controls class="w-full" />

        <div class="flex gap-2 pt-1">
          <button
            type="button"
            class="flex-1 h-10 rounded-full bg-secondary text-on-secondary font-label-md text-label-md font-bold flex items-center justify-center gap-2 disabled:opacity-60"
            :disabled="reviewingId === entry.id"
            @click="review(entry, 'verify')"
          >
            <span class="material-symbols-outlined text-[18px]">check_circle</span>
            Подтвердить
          </button>
          <button
            type="button"
            class="flex-1 h-10 rounded-full bg-error-container text-on-error-container font-label-md text-label-md font-bold flex items-center justify-center gap-2 disabled:opacity-60"
            :disabled="reviewingId === entry.id"
            @click="review(entry, 'reject')"
          >
            <span class="material-symbols-outlined text-[18px]">cancel</span>
            Отклонить
          </button>
        </div>
      </div>
    </template>
  </div>
</template>
