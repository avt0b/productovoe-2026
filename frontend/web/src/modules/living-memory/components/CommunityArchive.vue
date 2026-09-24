<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as archiveApi from '../api.js'

const { session } = useAuthSession()

const KIND_OPTIONS = [
  { id: 'event', label: 'Локальное событие' },
  { id: 'memory', label: 'Воспоминание очевидца' },
  { id: 'soldier_card', label: 'Карточка бойца' },
  { id: 'photo_story', label: 'Фото + история' },
]

const statusMeta = {
  verified: { label: 'Подтверждено', class: 'bg-secondary-fixed text-on-secondary-fixed', icon: 'verified' },
  pending: { label: 'На проверке', class: 'bg-tertiary-fixed text-on-tertiary-fixed', icon: 'hourglass_top' },
  rejected: { label: 'Отклонено', class: 'bg-error-container text-on-error-container', icon: 'cancel' },
}

const publicEntries = ref([])
const myEntries = ref([])
const loadStatus = ref('idle')

async function load() {
  loadStatus.value = 'loading'
  try {
    const requests = [archiveApi.listVerifiedEntries()]
    if (session.status === 'authenticated') requests.push(archiveApi.listMyEntries(session.accessToken))
    const [verified, mine] = await Promise.all(requests)
    // Если archive_service недоступен, шлюз иногда всё равно отвечает 200
    // не-JSON'ом (например SPA вместо API) — тело в этом случае не массив.
    publicEntries.value = Array.isArray(verified) ? verified : []
    myEntries.value = Array.isArray(mine) ? mine : []
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

onMounted(load)

// Публичная лента показывает только verified; свои записи (включая pending/
// rejected) добавляем поверх, без дублей по id.
const entries = computed(() => {
  const seen = new Set(myEntries.value.map((e) => e.id))
  return [...myEntries.value, ...publicEntries.value.filter((e) => !seen.has(e.id))]
})

function authorLabel(entry) {
  return entry.submitted_by === session.user?.id ? 'Вы' : 'Участник платформы'
}

const formOpen = ref(false)
const form = reactive({ kind: 'event', title: '', body: '' })
const submitStatus = ref('idle')
const error = ref('')

async function submit() {
  if (session.status !== 'authenticated') {
    error.value = 'Войдите, чтобы предложить событие'
    return
  }
  if (!form.title) {
    error.value = 'Укажите название'
    return
  }
  submitStatus.value = 'pending'
  error.value = ''
  try {
    const entry = await archiveApi.createEntry(session.accessToken, {
      kind: form.kind,
      title: form.title,
      body: form.body,
    })
    myEntries.value.unshift(entry)
    submitStatus.value = 'done'
    form.title = ''
    form.body = ''
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
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-5">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-2.5">
        <span class="material-symbols-outlined text-secondary text-[22px]">groups</span>
        <div class="flex flex-col">
          <span class="font-headline-sm text-headline-sm text-on-surface">Народный архив</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">
            Любой может предложить событие — краевед, наставник или модератор его подтверждает
            (archive_service)
          </span>
        </div>
      </div>
      <button
        class="px-4 py-2 rounded-full bg-secondary-fixed hover:bg-secondary-fixed-dim text-on-secondary-fixed font-label-md text-label-md font-bold flex items-center gap-1.5 shadow-sm transition-all"
        @click="formOpen = !formOpen"
      >
        <span class="material-symbols-outlined text-[18px]">add</span>
        <span>Предложить событие</span>
      </button>
    </div>

    <div v-if="formOpen" class="bg-surface-container-low rounded-DEFAULT p-4 flex flex-col gap-3">
      <template v-if="submitStatus !== 'done'">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="opt in KIND_OPTIONS"
            :key="opt.id"
            type="button"
            class="px-3 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all"
            :class="
              form.kind === opt.id
                ? 'bg-secondary text-on-secondary'
                : 'bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container'
            "
            @click="form.kind = opt.id"
          >
            {{ opt.label }}
          </button>
        </div>
        <input
          v-model="form.title"
          type="text"
          placeholder="Название события или объекта"
          class="w-full h-11 px-4 rounded-full bg-surface-container-lowest font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
        <textarea
          v-model="form.body"
          rows="3"
          placeholder="Что произошло, кто рассказал, есть ли фото или документы"
          class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-lowest font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
        />
        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>
        <button
          class="self-end px-5 py-2 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm flex items-center gap-2"
          :disabled="submitStatus === 'pending'"
          @click="submit"
        >
          <span v-if="submitStatus === 'pending'" class="material-symbols-outlined text-[18px] animate-spin">sync</span>
          <span>Отправить на проверку</span>
        </button>
      </template>
      <div v-else class="flex items-center gap-2 text-secondary font-label-md text-label-md font-bold py-2">
        <span class="material-symbols-outlined text-[20px]">check_circle</span>
        Событие отправлено на верификацию
      </div>
    </div>

    <p
      v-if="loadStatus === 'loaded' && !entries.length"
      class="font-body-md text-body-md text-on-surface-variant"
    >
      Записей пока нет — станьте первым, кто предложит событие.
    </p>

    <div v-else class="flex flex-col gap-2.5">
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-center justify-between gap-3"
      >
        <div class="flex flex-col min-w-0">
          <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ entry.title }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ authorLabel(entry) }}</span>
        </div>
        <span
          class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-bold flex items-center gap-1 shrink-0"
          :class="statusMeta[entry.status].class"
        >
          <span class="material-symbols-outlined text-[14px]">{{ statusMeta[entry.status].icon }}</span>
          {{ statusMeta[entry.status].label }}
        </span>
      </div>
    </div>
  </div>
</template>
