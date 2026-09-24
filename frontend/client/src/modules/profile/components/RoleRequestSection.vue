<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import { ApiError } from '@/core/api'
import { errorText, formatDate } from '@/core/format'
import type { SessionUser, UserRole } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SegmentTabs from '@/ui/SegmentTabs.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import {
  DOCUMENT_MAX_MB,
  REQUESTABLE_ROLES,
  ROLES,
  applicationText,
  clearRoleRequest,
  readRoleRequest,
  saveRoleRequest,
  uploadRoleDocument,
  type Profile,
  type RoleRequest,
} from '../data'

/**
 * Заявка на роль краеведа или поисковика.
 *
 * Роль выдаёт только администратор платформы, и очереди заявок в сервисах нет
 * (см. `data.ts`). Поэтому заявка уходит администратору сообщением, а
 * приложение запоминает на устройстве, что человек уже подавался: иначе он
 * собирал бы её заново каждый раз и не понимал, ждать ему или нет.
 */
const props = defineProps<{
  user: SessionUser
  /** Профиль — из него берём имя и город, чтобы человек не вводил их снова. */
  profile: Profile | null
}>()

const role = ref<UserRole>(REQUESTABLE_ROLES[0].role)

const tabs = computed(() =>
  REQUESTABLE_ROLES.map((item) => ({ value: item.role, title: ROLES[item.role].title, icon: ROLES[item.role].icon })),
)
const current = computed(() => REQUESTABLE_ROLES.find((item) => item.role === role.value) ?? REQUESTABLE_ROLES[0])
/** Роль уже есть — заявка не нужна, и форму показывать незачем. */
const alreadyGranted = computed(() => props.user.role === role.value)

// --- поданная заявка ---

const sent = ref<RoleRequest | null>(null)
const filling = ref(false)

// --- черновик заявки ---

const document = ref(current.value.documents[0].id)
const organization = ref('')
const experience = ref('')
const links = ref('')
const documentUrl = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const localPreview = ref<string | null>(null)
const uploading = ref(false)
const error = ref<string | null>(null)
const copied = ref(false)
/** Текст заявки, когда ни «Поделиться», ни буфер не сработали, — копировать руками. */
const manualText = ref<string | null>(null)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

const documentOptions = computed(() => current.value.documents.map((item) => ({ value: item.id, title: item.title })))

const missing = computed(() =>
  experience.value.trim().length < 20 ? 'Расскажите об опыте хотя бы парой предложений' : null,
)

function dropPreview(): void {
  if (localPreview.value) URL.revokeObjectURL(localPreview.value)
  localPreview.value = null
}

function reset(): void {
  dropPreview()
  document.value = current.value.documents[0].id
  organization.value = ''
  experience.value = ''
  links.value = ''
  documentUrl.value = null
  error.value = null
  manualText.value = null
  filling.value = false
}

/** Переключили роль — показываем её заявку и чистый черновик. */
watch(
  [role, () => props.user.id],
  () => {
    sent.value = readRoleRequest(role.value, props.user.id)
    reset()
  },
  { immediate: true },
)

/** Снимок уходит в хранилище сразу: к отправке адрес уже готов. */
async function pickDocument(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  dropPreview()
  localPreview.value = URL.createObjectURL(file)
  error.value = null
  uploading.value = true
  try {
    documentUrl.value = await uploadRoleDocument(file)
  } catch (reason) {
    dropPreview()
    // 503 — хранилище не поднято: заявку это не отменяет, документ дошлют отдельно.
    error.value =
      reason instanceof ApiError && reason.status === 503
        ? 'Хранилище фото сейчас недоступно. Отправьте заявку без снимка — документ покажете отдельно.'
        : errorText(reason)
  } finally {
    uploading.value = false
  }
}

function removeDocument(): void {
  dropPreview()
  documentUrl.value = null
  error.value = null
}

function textOf(request: RoleRequest): string {
  return applicationText(
    request,
    props.profile?.display_name || props.user.name,
    props.user.id,
    props.profile?.city || props.user.city,
  )
}

/**
 * Передать заявку администратору: системным окном «Поделиться», а где его нет
 * (в APK Web Share API не работает) — через буфер обмена.
 *
 * `cancelled` — человек сам закрыл окно отправки; `failed` — ни окна, ни
 * буфера: тогда показываем текст заявки, чтобы его можно было скопировать
 * руками, а не терять всё, что человек написал.
 */
async function deliver(request: RoleRequest): Promise<'sent' | 'cancelled' | 'failed'> {
  const text = textOf(request)
  if (navigator.share) {
    try {
      await navigator.share({ title: `Заявка на роль «${ROLES[request.role].title}»`, text })
      return 'sent'
    } catch (reason) {
      if (reason instanceof DOMException && reason.name === 'AbortError') return 'cancelled'
    }
  }
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => (copied.value = false), 4000)
    return 'sent'
  } catch {
    return 'failed'
  }
}

async function send(): Promise<void> {
  if (missing.value || uploading.value) return
  const request: RoleRequest = {
    role: role.value,
    document: document.value,
    documentUrl: documentUrl.value,
    organization: organization.value.trim(),
    experience: experience.value.trim(),
    links: links.value.trim(),
    sentAt: new Date().toISOString(),
  }
  const outcome = await deliver(request)
  if (outcome === 'cancelled') return
  saveRoleRequest(props.user.id, request)
  sent.value = request
  reset()
  if (outcome === 'failed') manualText.value = textOf(request)
}

/** Передать ещё раз — администратор мог не увидеть сообщение. */
async function resend(): Promise<void> {
  const request = sent.value
  if (!request) return
  manualText.value = (await deliver(request)) === 'failed' ? textOf(request) : null
}

function withdraw(): void {
  clearRoleRequest(role.value, props.user.id)
  sent.value = null
  manualText.value = null
}

onBeforeUnmount(() => {
  clearTimeout(copiedTimer)
  dropPreview()
})
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">Доступ по заявке</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">Стать краеведом или поисковиком</h2>
    </div>

    <div class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <SegmentTabs v-model="role" :tabs="tabs" label="Роль, на которую подаём заявку" id-prefix="role-request" />

      <div :id="`role-request-${role}`" role="tabpanel" :aria-labelledby="`role-request-tab-${role}`" class="flex flex-col gap-space-md">
        <div class="flex items-start gap-space-sm">
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed"
            aria-hidden="true"
          >
            <MsIcon :name="ROLES[role].icon" :size="20" />
          </span>
          <div class="min-w-0">
            <p class="font-archival text-archival uppercase text-on-surface-variant">{{ current.who }}</p>
            <p class="font-headline-sm text-headline-sm text-on-surface">Что откроет роль</p>
          </div>
        </div>

        <ul class="flex flex-col gap-1">
          <li v-for="item in ROLES[role].gives" :key="item" class="flex items-start gap-space-xs font-body-sm text-body-sm text-on-surface">
            <MsIcon name="check" :size="18" class="shrink-0 text-secondary" />
            {{ item }}
          </li>
        </ul>

        <InlineNotice v-if="alreadyGranted" tone="success">
          Роль «{{ ROLES[role].title }}» у вас уже есть — заявка не нужна.
        </InlineNotice>

        <template v-else>
          <InlineNotice v-if="sent" tone="success">
            Заявка отправлена {{ formatDate(sent.sentAt) }} — роль выдаёт администратор платформы. Когда он подтвердит,
            выйдите и войдите заново: новые возможности появятся.
          </InlineNotice>
          <template v-if="manualText">
            <InlineNotice tone="error">
              Передать заявку автоматически не вышло — ни окна отправки, ни буфера обмена. Скопируйте текст и отправьте
              администратору сами.
            </InlineNotice>
            <textarea
              :value="manualText"
              readonly
              rows="6"
              aria-label="Текст заявки"
              class="w-full resize-none rounded-DEFAULT bg-surface-container-low p-space-sm font-body-sm text-body-sm text-on-surface"
            />
          </template>
          <InlineNotice v-else tone="info">
            Роль подтверждает администратор платформы. Заявка уйдёт ему сообщением — приложите документ, так быстрее.
          </InlineNotice>

          <div class="flex flex-wrap gap-space-xs">
            <button
              v-if="sent"
              type="button"
              class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
              @click="resend"
            >
              <MsIcon :name="copied ? 'check' : 'send'" :size="18" />
              {{ copied ? 'Текст скопирован' : 'Передать ещё раз' }}
            </button>
            <button
              v-if="sent"
              type="button"
              class="rounded-full px-space-md py-2 font-label-md text-label-md text-on-surface-variant active:scale-95"
              @click="withdraw"
            >
              Отозвать заявку
            </button>
            <button
              v-else
              type="button"
              class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
              :aria-expanded="filling"
              @click="filling ? reset() : (filling = true)"
            >
              <MsIcon :name="filling ? 'close' : 'edit_note'" :size="18" />
              {{ filling ? 'Отменить' : 'Подать заявку' }}
            </button>
          </div>

          <!-- Форма раскрывается высотой: `v-if` дёргал бы карточку на полэкрана. -->
          <div
            class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
            :class="filling && !sent ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
            :inert="!filling || sent !== null"
          >
            <form class="flex flex-col gap-space-md overflow-hidden" @submit.prevent="send">
              <div class="pt-space-xs">
                <FormSelect v-model="document" label="Чем подтвердите" :options="documentOptions" icon="fact_check" />
              </div>

              <div class="flex items-center gap-space-md">
                <span
                  class="relative flex h-20 w-16 shrink-0 items-center justify-center overflow-hidden rounded-DEFAULT border border-dashed border-outline-variant bg-surface-container-low text-on-surface-variant"
                >
                  <img
                    v-if="localPreview"
                    :src="localPreview"
                    alt=""
                    class="h-full w-full object-cover"
                    :class="{ 'opacity-50': uploading }"
                  />
                  <MsIcon v-else name="description" :size="24" />
                  <MsIcon v-if="uploading" name="progress_activity" :size="20" class="absolute animate-spin" />
                </span>
                <div class="flex min-w-0 flex-col items-start gap-space-xs">
                  <button
                    type="button"
                    class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
                    :disabled="uploading"
                    @click="fileInput?.click()"
                  >
                    <MsIcon name="add_a_photo" :size="18" />
                    {{ localPreview ? 'Заменить снимок' : 'Снимок документа' }}
                  </button>
                  <button
                    v-if="localPreview"
                    type="button"
                    class="px-space-xs font-label-md text-label-md text-on-surface-variant active:scale-95"
                    @click="removeDocument"
                  >
                    Убрать снимок
                  </button>
                  <p class="font-body-sm text-body-sm text-on-surface-variant">
                    Необязательно, JPEG, PNG или WebP, до {{ DOCUMENT_MAX_MB }} МБ
                  </p>
                </div>
              </div>
              <input
                ref="fileInput"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                class="sr-only"
                tabindex="-1"
                @change="pickDocument"
              />

              <FormInput
                v-model="organization"
                label="Отряд, музей или школа"
                icon="flag"
                :maxlength="200"
                :placeholder="role === 'searcher' ? 'Поисковый отряд «Высота», Орёл' : 'Кромской краеведческий музей'"
              />
              <FormTextarea
                v-model="experience"
                label="Опыт"
                :rows="3"
                :maxlength="2000"
                :placeholder="
                  role === 'searcher'
                    ? 'Сколько лет в поиске, в каких «Вахтах Памяти» участвовали, с каким отрядом'
                    : 'Сколько лет занимаетесь краеведением, какие темы, с какими архивами работали'
                "
                required
              />
              <FormInput v-model="links" label="Публикации и ссылки" icon="link" :maxlength="500" placeholder="Статьи, книги, страница отряда" />

              <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
              <p v-else class="text-center font-body-sm text-body-sm text-on-surface-variant">
                {{
                  uploading
                    ? 'Загружаем снимок — отправим заявку, как только он дойдёт'
                    : (missing ?? 'Откроется окно «Поделиться» — выберите, куда отправить заявку администратору')
                }}
              </p>

              <button
                type="submit"
                class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
                :disabled="missing !== null || uploading"
              >
                <MsIcon name="send" :size="18" />
                <span>Отправить заявку</span>
              </button>
            </form>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>
