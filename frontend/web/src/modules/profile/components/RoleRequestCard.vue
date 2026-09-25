<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import { useProfileStore } from '../profileStore.js'
import { uploadVerificationDocument } from '../api.js'

const { session } = useAuthSession()
const { profile } = useProfileStore()

// Роли реально разное разблокируют на бэке: поисковик — создаёт отряд и
// заявки на сбор/выезд, краевед — ведёт экскурсии; точки на карте и
// подтверждение записей «Живой памяти» доступны обеим ролям. Но саму роль
// назначает только администратор через админку — очереди заявок
// «пользователь просит роль, модератор подтверждает» на бэке нет вообще.
// Поэтому это честный фронтовый черновик: документ реально загружается, а
// сам факт заявки — только в этом браузере (ДЕМО).
const ROLES = [
  {
    id: 'local_historian',
    label: 'Краевед',
    icon: 'auto_stories',
    unlocks: 'Проводить экскурсии, добавлять точки на карту и подтверждать записи «Живой памяти»',
    docTypes: [
      { id: 'membership', label: 'Членский билет краеведческого общества' },
      { id: 'diploma', label: 'Диплом/документ об образовании' },
      { id: 'other', label: 'Другой документ' },
    ],
  },
  {
    id: 'searcher',
    label: 'Поисковик',
    icon: 'travel_explore',
    unlocks: 'Создавать отряд, заявки на сбор и выезд в «Штабе», добавлять точки на карту и подтверждать записи «Живой памяти»',
    docTypes: [
      { id: 'membership', label: 'Удостоверение поискового отряда' },
      { id: 'certificate', label: 'Сертификат участника «Вахты Памяти»' },
      { id: 'other', label: 'Другой документ' },
    ],
  },
]

const activeIndex = ref(0)
const activeRole = computed(() => ROLES[activeIndex.value])

function go(delta) {
  activeIndex.value = (activeIndex.value + delta + ROLES.length) % ROLES.length
}

// --- свайп (тач) ---
let touchStartX = null
function onTouchStart(event) {
  touchStartX = event.touches[0].clientX
}
function onTouchEnd(event) {
  if (touchStartX === null) return
  const delta = event.changedTouches[0].clientX - touchStartX
  touchStartX = null
  if (Math.abs(delta) < 40) return
  go(delta < 0 ? 1 : -1)
}

// --- заявки по каждой роли отдельно ---
function storageKey(roleId, profileId) {
  return `marshruty.role-request.${roleId}.${profileId}`
}

function loadSubmission(roleId, profileId) {
  try {
    const raw = localStorage.getItem(storageKey(roleId, profileId))
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const submissions = reactive({})
watch(
  () => profile.data?.id,
  (id) => {
    if (!id) return
    for (const role of ROLES) submissions[role.id] = loadSubmission(role.id, id)
  },
  { immediate: true },
)

const file = ref(null)
const docType = ref(ROLES[0].docTypes[0].id)
const note = ref('')
const status = ref('idle') // idle | uploading | error
const error = ref('')

watch(activeRole, (role) => {
  file.value = null
  note.value = ''
  error.value = ''
  status.value = 'idle'
  docType.value = role.docTypes[0].id
})

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
    localStorage.setItem(storageKey(activeRole.value.id, profile.data.id), JSON.stringify(record))
    submissions[activeRole.value.id] = record
    file.value = null
    note.value = ''
    status.value = 'idle'
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось загрузить документ'
  }
}

function withdraw() {
  localStorage.removeItem(storageKey(activeRole.value.id, profile.data.id))
  submissions[activeRole.value.id] = null
}

function docTypeLabel(role, id) {
  return role.docTypes.find((d) => d.id === id)?.label ?? id
}
</script>

<template>
  <div
    v-if="session.status === 'authenticated'"
    class="relative bg-surface-container-lowest p-6 rounded-2xl shadow-document flex flex-col overflow-hidden"
  >
    <div class="flex items-center justify-between gap-3 mb-2">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-10 h-10 rounded-full bg-surface-container-high text-on-surface flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-[20px]">{{ activeRole.icon }}</span>
        </div>
        <div class="flex flex-col min-w-0">
          <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface truncate">Заявка на роль: {{ activeRole.label }}</h2>
          <span class="font-body-sm text-body-sm text-on-surface-variant">Свайпните карточку для другой роли</span>
        </div>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <button
          type="button"
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors"
          @click="go(-1)"
        >
          <span class="material-symbols-outlined text-[18px]">chevron_left</span>
        </button>
        <button
          type="button"
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors"
          @click="go(1)"
        >
          <span class="material-symbols-outlined text-[18px]">chevron_right</span>
        </button>
      </div>
    </div>

    <div class="flex items-center justify-center gap-1.5 mb-3">
      <span
        v-for="(role, i) in ROLES"
        :key="role.id"
        class="h-1.5 rounded-full transition-all"
        :class="i === activeIndex ? 'w-6 bg-primary' : 'w-1.5 bg-surface-container-high'"
      />
    </div>

    <div class="flex flex-col" @touchstart="onTouchStart" @touchend="onTouchEnd">
      <p class="font-body-sm text-body-sm text-on-surface-variant mb-3">
        <span class="font-bold text-on-surface">Что даёт роль «{{ activeRole.label }}»:</span> {{ activeRole.unlocks }}.
      </p>

      <div v-if="profile.data?.role === activeRole.id" class="flex items-center gap-2 bg-secondary-container text-on-secondary-container px-4 py-3 rounded-DEFAULT">
        <span class="material-symbols-outlined text-[20px]">check_circle</span>
        <span class="font-body-sm text-body-sm font-bold">У вас уже роль «{{ activeRole.label }}»</span>
      </div>

      <template v-else>
        <p class="font-body-sm text-body-sm text-on-surface-variant mb-3">
          Приложите подтверждающий документ — модератор вручную присвоит роль через админ-панель.
          <span class="font-bold">
            Демо: очереди заявок на бэкенде пока нет, заявка сохраняется только в этом браузере.
          </span>
        </p>

        <div v-if="submissions[activeRole.id]" class="flex flex-col gap-3">
          <div class="flex items-center gap-3 bg-tertiary-fixed text-on-tertiary-fixed px-4 py-3 rounded-DEFAULT">
            <span class="material-symbols-outlined text-[20px]">hourglass_top</span>
            <div class="flex flex-col min-w-0">
              <span class="font-body-sm text-body-sm font-bold">Заявка отправлена, ожидает проверки (демо)</span>
              <span class="font-label-sm text-label-sm opacity-80">
                {{ docTypeLabel(activeRole, submissions[activeRole.id].docType) }} ·
                {{ new Date(submissions[activeRole.id].submittedAt).toLocaleString('ru-RU') }}
              </span>
            </div>
          </div>
          <a :href="submissions[activeRole.id].documentUrl" target="_blank" rel="noopener" class="block">
            <img :src="submissions[activeRole.id].documentUrl" alt="Загруженный документ" class="max-h-40 rounded-DEFAULT object-cover" />
          </a>
          <p v-if="submissions[activeRole.id].note" class="font-body-sm text-body-sm text-on-surface-variant">
            {{ submissions[activeRole.id].note }}
          </p>
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
              <option v-for="d in activeRole.docTypes" :key="d.id" :value="d.id">{{ d.label }}</option>
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
  </div>
</template>
