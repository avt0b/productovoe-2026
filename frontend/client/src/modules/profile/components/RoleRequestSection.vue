<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { ApiError } from '@/core/api'
import { ORGANIZATION_KINDS, organizationKind, type OrganizationKind } from '@/core/services/organizations'
import { errorText, formatDate } from '@/core/format'
import type { SessionUser, UserRole } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SegmentTabs from '@/ui/SegmentTabs.vue'
import FormInput from '@/ui/form/FormInput.vue'

import OrganizationPicker from './OrganizationPicker.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import {
  DOCUMENT_MAX_MB,
  REQUESTABLE_ROLES,
  ROLES,
  myRoleApplications,
  submitRoleApplication,
  uploadRoleDocument,
  type Profile,
  type RoleApplication,
  type SquadOption,
} from '../data'

/**
 * Заявка на роль краеведа или поисковика.
 *
 * Заявки живут в `user_service` (`/role-applications`), решение принимает
 * администратор платформы: он же выставляет роль в `auth_service`. Поэтому
 * здесь показываем и поданную заявку, и ответ по ней — с причиной отказа,
 * если администратор её написал.
 */
const props = defineProps<{
  user: SessionUser
  /** Профиль — из него берём имя, чтобы человек не вводил его снова, и город. */
  profile: Profile | null
  /** Отряды, музеи и школы из «Штаба». */
  organizations: SquadOption[]
}>()

/** Поисковику первыми нужны отряды, краеведу — музеи. */
const ORDER: Record<string, readonly OrganizationKind[]> = {
  searcher: ['squad', 'school', 'museum'],
  local_historian: ['museum', 'school', 'squad'],
}

const role = ref<UserRole>(REQUESTABLE_ROLES[0].role)

const tabs = computed(() =>
  REQUESTABLE_ROLES.map((item) => ({ value: item.role, title: ROLES[item.role].title, icon: ROLES[item.role].icon })),
)
const current = computed(() => REQUESTABLE_ROLES.find((item) => item.role === role.value) ?? REQUESTABLE_ROLES[0])
/** Роль уже есть — заявка не нужна, и форму показывать незачем. */
const alreadyGranted = computed(() => props.user.role === role.value)

// --- поданные заявки ---

const applications = ref<RoleApplication[]>([])
const loading = ref(true)
const filling = ref(false)

/** Последняя заявка на выбранную роль — по ней и показываем состояние. */
const application = computed(() => applications.value.find((item) => item.requested_role === role.value) ?? null)
const pending = computed(() => application.value?.status === 'pending')

// --- черновик заявки ---

const document = ref(current.value.documents[0].id)
const fullName = ref('')
const contact = ref('')
/** id выбранной организации, `other` — вписали свою. */
const organizationId = ref<string | null>(null)
const organization = ref('')
const city = computed(() => props.profile?.city?.trim() || props.user.city || '')
const chosenOrganization = computed(() => props.organizations.find((item) => item.id === organizationId.value) ?? null)
const experience = ref('')
const links = ref('')
const documentUrl = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const localPreview = ref<string | null>(null)
const uploading = ref(false)
const sending = ref(false)
const error = ref<string | null>(null)
/**
 * Нажали «Отправить», а графы не заполнены. Кнопка при этом не выключается:
 * выключенная выглядела почти как обычная, и казалось, что она просто не
 * нажимается, — лучше нажать и прочитать, чего не хватает.
 */
const tried = ref(false)
const shownError = computed(() => error.value ?? (tried.value ? missing.value : null))

const documentOptions = computed(() => current.value.documents.map((item) => ({ value: item.id, title: item.title })))

const missing = computed(() => {
  if (!fullName.value.trim()) return 'Укажите имя и фамилию — так администратор сверит их с документом'
  if (!contact.value.trim()) return 'Оставьте способ связи: телефон или телеграм'
  // Поисковик — всегда из какого-то отряда, музея или клуба; краевед бывает и сам по себе.
  if (role.value === 'searcher' && !chosenOrganization.value && !(organizationId.value === 'other' && organization.value.trim())) {
    return 'Выберите свой отряд, музей или школу — или впишите название'
  }
  if (experience.value.trim().length < 20) return 'Расскажите об опыте хотя бы парой предложений'
  return null
})

function dropPreview(): void {
  if (localPreview.value) URL.revokeObjectURL(localPreview.value)
  localPreview.value = null
}

function reset(): void {
  dropPreview()
  document.value = current.value.documents[0].id
  fullName.value = props.profile?.display_name || props.user.name
  contact.value = ''
  organizationId.value = null
  organization.value = ''
  experience.value = ''
  links.value = ''
  documentUrl.value = null
  error.value = null
  tried.value = false
  filling.value = false
}

async function load(): Promise<void> {
  try {
    applications.value = await myRoleApplications()
  } catch (reason) {
    // Заявок не видно — это не повод прятать форму: подать её всё равно можно.
    console.warn('[profile] заявки на роль не загрузились', reason)
  } finally {
    loading.value = false
  }
}

onMounted(load)

/** Переключили роль — чистый черновик под неё. */
watch([role, () => props.user.id], reset, { immediate: true })

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

/**
 * Сервис хранит доказательства одним текстом, поэтому графы формы собираем в
 * него сами: администратор читает заявку целиком, а не по полям.
 */
function evidenceText(): string {
  const documents = current.value.documents
  const title = documents.find((item) => item.id === document.value)?.title ?? 'Документ'
  const chosen = chosenOrganization.value
  const place = chosen
    ? `${chosen.name} (${ORGANIZATION_KINDS[organizationKind(chosen.kind)].title}${chosen.region ? `, ${chosen.region}` : ''}, id ${chosen.id})`
    : organizationId.value === 'other'
      ? `${organization.value.trim()} — нет в списке «Штаба»`
      : ''
  return [
    place ? `Отряд, музей, школа: ${place}` : '',
    `Опыт: ${experience.value.trim()}`,
    links.value.trim() ? `Публикации и ссылки: ${links.value.trim()}` : '',
    `Документ: ${title}${documentUrl.value ? '' : ' — покажу отдельно'}`,
  ]
    .filter(Boolean)
    .join('\n')
}

async function send(): Promise<void> {
  if (uploading.value || sending.value) return
  if (missing.value) {
    tried.value = true
    return
  }
  sending.value = true
  error.value = null
  try {
    const created = await submitRoleApplication({
      requested_role: role.value as 'searcher' | 'local_historian',
      full_name: fullName.value.trim(),
      contact: contact.value.trim(),
      evidence: evidenceText(),
      evidence_url: documentUrl.value,
    })
    applications.value = [created, ...applications.value.filter((item) => item.id !== created.id)]
    reset()
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    sending.value = false
  }
}

onBeforeUnmount(dropPreview)
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
          <div
            v-if="loading"
            class="flex items-center gap-space-xs font-label-md text-label-md text-on-surface-variant"
            role="status"
          >
            <MsIcon name="progress_activity" :size="18" class="animate-spin" />
            Смотрим, не подавали ли вы заявку…
          </div>

          <template v-else-if="application">
            <InlineNotice v-if="application.status === 'pending'" tone="info">
              Заявка подана {{ formatDate(application.created_at) }} — её рассматривает администратор платформы. Когда он
              одобрит, выйдите и войдите заново: новые возможности появятся.
            </InlineNotice>
            <InlineNotice v-else-if="application.status === 'approved'" tone="success">
              Заявку одобрили {{ formatDate(application.created_at) }}. Если новые возможности ещё не появились — выйдите
              и войдите заново.
            </InlineNotice>
            <InlineNotice v-else tone="error">
              Заявку отклонили.{{ application.review_note ? ` Причина: ${application.review_note}` : '' }} Заявку можно
              подать заново — добавьте то, чего не хватило.
            </InlineNotice>
          </template>

          <InlineNotice v-else tone="info">
            Роль подтверждает администратор платформы. Приложите документ — так быстрее.
          </InlineNotice>

          <div v-if="!pending" class="flex flex-wrap gap-space-xs">
            <button
              type="button"
              class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
              :aria-expanded="filling"
              @click="filling ? reset() : (filling = true)"
            >
              <MsIcon :name="filling ? 'close' : 'edit_note'" :size="18" />
              {{ filling ? 'Отменить' : application ? 'Подать заново' : 'Подать заявку' }}
            </button>
          </div>

          <!-- Форма раскрывается высотой: `v-if` дёргал бы карточку на полэкрана. -->
          <div
            class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
            :class="filling && !pending ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
            :inert="!filling || pending"
          >
            <form class="flex flex-col gap-space-md overflow-hidden" novalidate @submit.prevent="send">
              <div class="flex flex-col gap-space-md pt-space-xs">
                <FormInput
                  v-model="fullName"
                  label="Имя и фамилия"
                  icon="badge"
                  :maxlength="255"
                  placeholder="Ирина Осипова"
                  required
                />
                <FormInput
                  v-model="contact"
                  label="Как с вами связаться"
                  icon="call"
                  :maxlength="300"
                  placeholder="Телефон или телеграм"
                  required
                />
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

              <OrganizationPicker
                v-model="organizationId"
                v-model:other-name="organization"
                :organizations="organizations"
                :city="city"
                :order="ORDER[role] ?? ORDER.searcher"
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

              <InlineNotice v-if="shownError" tone="error">{{ shownError }}</InlineNotice>
              <p v-else class="text-center font-body-sm text-body-sm text-on-surface-variant">
                {{
                  uploading
                    ? 'Загружаем снимок — отправим заявку, как только он дойдёт'
                    : (missing ?? 'Заявка уйдёт администратору платформы — ответ придёт сюда же')
                }}
              </p>

              <button
                type="submit"
                class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
                :disabled="uploading || sending"
              >
                <MsIcon :name="sending ? 'progress_activity' : 'send'" :size="18" :class="{ 'animate-spin': sending }" />
                <span>Отправить заявку</span>
              </button>
            </form>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>
