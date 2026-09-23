<script setup lang="ts">
import { computed, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText, formatDate } from '@/core/format'
import { can, type SessionUser, type UserRole } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import {
  EVERYONE_CAN,
  ROLES,
  ROLE_ORDER,
  applicationText,
  fetchProfileById,
  setUserRole,
  verifyProfile,
  type Profile,
  type RoleApplication,
} from '../data'

/**
 * Роли и что они дают. Экран входа больше не спрашивает, краевед ли человек, —
 * роль получают здесь: заявитель готовит заявку и показывает жетон, краевед
 * подтверждает профиль, администратор платформы выдаёт роль.
 */
const props = defineProps<{
  user: SessionUser
  profile: Profile | null
}>()

const emit = defineEmits<{ 'open-token': [] }>()

const role = computed(() => props.user.role ?? 'family')
const isVerifier = computed(() => can.verifyArchive(props.user))
const othersOpen = ref(false)

// --- заявка на роль краеведа ---

const APPLICATION_KEY = computed(() => `marshruty.client.profile.application.${props.user.id}`)

function readSentAt(): string | null {
  try {
    return localStorage.getItem(APPLICATION_KEY.value)
  } catch {
    return null
  }
}

const applying = ref(false)
const application = ref<RoleApplication>({ experience: '', organization: '', links: '' })
/** Когда заявку отправили — запоминаем на телефоне, чтобы не собирать её второй раз. */
const sentAt = ref<string | null>(readSentAt())
const copied = ref(false)

const applicationMissing = computed(() =>
  application.value.experience.trim().length < 20 ? 'Расскажите об опыте хотя бы парой предложений' : null,
)

/**
 * Заявки в сервисах не принимают — роль выдаёт администратор платформы.
 * Поэтому заявка уходит сообщением: системным окном «Поделиться» или через буфер.
 */
async function sendApplication(): Promise<void> {
  if (applicationMissing.value) return
  const text = applicationText(
    props.profile?.display_name || props.user.name,
    props.user.id,
    props.profile?.city || props.user.city,
    application.value,
  )
  try {
    if (navigator.share) await navigator.share({ title: 'Заявка на роль краеведа', text })
    else {
      await navigator.clipboard.writeText(text)
      copied.value = true
    }
  } catch {
    return
  }
  const now = new Date().toISOString()
  sentAt.value = now
  applying.value = false
  try {
    localStorage.setItem(APPLICATION_KEY.value, now)
  } catch {
    /* приватный режим — отметка проживёт до закрытия */
  }
}

// --- краевед подтверждает, администратор выдаёт роль ---

const tokenId = ref('')
const found = ref<Profile | null>(null)
const looking = ref(false)
const acting = ref(false)
const toolError = ref<string | null>(null)
const toolNotice = ref<string | null>(null)
const grantRole = ref<UserRole | ''>('local_historian')

const tokenValid = computed(() => /^[0-9a-f-]{8,36}$/i.test(tokenId.value.trim()))
const roleOptions = ROLE_ORDER.map((value) => ({ value, title: ROLES[value].title }))

async function lookUp(): Promise<void> {
  if (!tokenValid.value || looking.value) return
  looking.value = true
  toolError.value = null
  toolNotice.value = null
  found.value = null
  try {
    found.value = await fetchProfileById(tokenId.value.trim())
  } catch (reason) {
    toolError.value = reason instanceof ApiError && reason.status === 404 ? 'Исследователь с таким жетоном не найден' : errorText(reason)
  } finally {
    looking.value = false
  }
}

async function setVerified(value: boolean): Promise<void> {
  if (!found.value || acting.value) return
  acting.value = true
  toolError.value = null
  try {
    found.value = await verifyProfile(found.value.id, value)
    toolNotice.value = value ? 'Профиль подтверждён — у исследователя появится значок' : 'Подтверждение снято'
  } catch (reason) {
    toolError.value = errorText(reason)
  } finally {
    acting.value = false
  }
}

async function grant(): Promise<void> {
  if (!found.value || !grantRole.value || acting.value) return
  acting.value = true
  toolError.value = null
  try {
    await setUserRole(found.value.id, grantRole.value)
    toolNotice.value = `Роль «${ROLES[grantRole.value].title}» выдана. Она заработает, когда человек войдёт заново.`
  } catch (reason) {
    toolError.value = errorText(reason)
  } finally {
    acting.value = false
  }
}
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">Доступ</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">Роль и что она даёт</h2>
    </div>

    <div class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div class="flex items-center gap-space-sm">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container" aria-hidden="true">
          <MsIcon :name="ROLES[role].icon" :size="20" filled />
        </span>
        <div class="min-w-0">
          <p class="font-archival text-archival uppercase text-on-surface-variant">Ваша роль</p>
          <p class="font-headline-sm text-headline-sm text-on-surface">{{ ROLES[role].title }}</p>
        </div>
      </div>
      <ul class="flex flex-col gap-1">
        <li v-for="item in [...ROLES[role].gives, ...EVERYONE_CAN]" :key="item" class="flex items-start gap-space-xs font-body-sm text-body-sm text-on-surface">
          <MsIcon name="check" :size="18" class="shrink-0 text-secondary" />
          {{ item }}
        </li>
      </ul>

      <button
        type="button"
        class="flex items-center justify-between gap-space-sm border-t border-outline-variant/60 pt-space-sm text-left font-label-md text-label-md text-on-surface-variant"
        :aria-expanded="othersOpen"
        @click="othersOpen = !othersOpen"
      >
        Что дают другие роли
        <MsIcon name="expand_more" :size="18" class="transition-transform duration-300" :class="{ 'rotate-180': othersOpen }" />
      </button>
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="othersOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!othersOpen"
      >
        <ul class="flex flex-col gap-space-sm overflow-hidden">
          <li v-for="other in ROLE_ORDER.filter((value) => value !== role && ROLES[value].gives.length)" :key="other" class="flex items-start gap-space-sm">
            <MsIcon :name="ROLES[other].icon" :size="18" class="mt-0.5 shrink-0 text-on-surface-variant" />
            <div class="min-w-0">
              <p class="font-label-md text-label-md text-on-surface">{{ ROLES[other].title }}</p>
              <p class="font-body-sm text-body-sm text-on-surface-variant">{{ ROLES[other].gives.join(' · ') }}</p>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- Стать краеведом: заявка администратору и подтверждение профиля по жетону. -->
    <div v-if="!isVerifier" class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div class="flex items-start gap-space-sm">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed" aria-hidden="true">
          <MsIcon name="history_edu" :size="20" />
        </span>
        <div class="min-w-0">
          <p class="font-archival text-archival uppercase text-on-surface-variant">Для учителей, музейщиков, поисковиков</p>
          <p class="font-headline-sm text-headline-sm text-on-surface">Стать краеведом</p>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Краевед проверяет народный архив и водит экскурсии. Роль выдаёт администратор платформы по заявке.
          </p>
        </div>
      </div>

      <InlineNotice v-if="sentAt && !applying" tone="success">
        Заявка отправлена {{ formatDate(sentAt) }}. Когда администратор выдаст роль, выйдите и войдите заново — появятся новые
        возможности.
      </InlineNotice>

      <div class="flex flex-wrap gap-space-xs">
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          :aria-expanded="applying"
          @click="applying = !applying"
        >
          <MsIcon name="edit_note" :size="18" />
          {{ sentAt ? 'Отправить заявку ещё раз' : 'Подать заявку' }}
        </button>
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="emit('open-token')"
        >
          <MsIcon name="badge" :size="18" />
          Жетон для краеведа
        </button>
      </div>

      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="applying ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!applying"
      >
        <form class="flex flex-col gap-space-md overflow-hidden" @submit.prevent="sendApplication">
          <div class="flex flex-col gap-space-md pt-space-sm">
            <FormInput v-model="application.organization" label="Музей, школа или отряд" :maxlength="200" placeholder="Кромской краеведческий музей" />
            <FormTextarea
              v-model="application.experience"
              label="Опыт"
              :rows="3"
              :maxlength="2000"
              placeholder="Сколько лет занимаетесь краеведением, какие темы, с какими архивами работали"
              required
            />
            <FormInput v-model="application.links" label="Публикации и ссылки" :maxlength="500" placeholder="Статьи, книги, страница музея" />
          </div>
          <p v-if="applicationMissing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ applicationMissing }}</p>
          <p v-else class="text-center font-body-sm text-body-sm text-on-surface-variant">
            {{ copied ? 'Текст заявки скопирован — вставьте его в письмо или сообщение администратору' : 'Откроется окно «Поделиться» — выберите, куда отправить' }}
          </p>
          <button
            type="submit"
            class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
            :disabled="applicationMissing !== null"
          >
            <MsIcon name="send" :size="18" />
            <span>Отправить заявку</span>
          </button>
        </form>
      </div>
    </div>

    <!-- Краевед, наставник, модератор: подтвердить исследователя; администратор — ещё и выдать роль. -->
    <div v-else class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div class="flex items-start gap-space-sm">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed" aria-hidden="true">
          <MsIcon name="how_to_reg" :size="20" />
        </span>
        <div class="min-w-0">
          <p class="font-archival text-archival uppercase text-on-surface-variant">По жетону исследователя</p>
          <p class="font-headline-sm text-headline-sm text-on-surface">{{ user.isRoot ? 'Подтвердить и выдать роль' : 'Подтвердить исследователя' }}</p>
          <p class="font-body-sm text-body-sm text-on-surface-variant">Попросите номер жетона — он в профиле человека, под значком жетона.</p>
        </div>
      </div>

      <form class="flex items-end gap-space-sm" @submit.prevent="lookUp">
        <div class="min-w-0 flex-1">
          <FormInput v-model="tokenId" label="Номер жетона" :maxlength="36" placeholder="3f54e213-0262-…" />
        </div>
        <button
          type="submit"
          class="mb-0.5 flex shrink-0 items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
          :disabled="!tokenValid || looking"
        >
          <MsIcon :name="looking ? 'progress_activity' : 'search'" :size="18" :class="{ 'animate-spin': looking }" />
          Найти
        </button>
      </form>

      <div v-if="found" class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
        <div class="flex items-center gap-space-sm">
          <MsIcon :name="found.is_verified ? 'verified' : 'person'" :size="20" :filled="found.is_verified" :class="found.is_verified ? 'text-tertiary' : 'text-on-surface-variant'" />
          <div class="min-w-0">
            <p class="truncate font-label-lg text-label-lg text-on-surface">{{ found.display_name || 'Имя не указано' }}</p>
            <p class="truncate font-body-sm text-body-sm text-on-surface-variant">
              {{ [ROLES[(found.role as UserRole)]?.title ?? found.role, found.city].filter(Boolean).join(' · ') }}
            </p>
          </div>
        </div>
        <p v-if="found.bio" class="line-clamp-3 font-body-sm text-body-sm text-on-surface-variant">{{ found.bio }}</p>
        <button
          type="button"
          class="flex items-center justify-center gap-space-xs rounded-full py-2.5 font-label-md text-label-md active:scale-[0.99] disabled:opacity-60"
          :class="found.is_verified ? 'bg-surface-container-high text-on-surface' : 'bg-tertiary text-on-tertiary'"
          :disabled="acting"
          @click="setVerified(!found.is_verified)"
        >
          <MsIcon :name="found.is_verified ? 'remove_moderator' : 'verified'" :size="18" />
          {{ found.is_verified ? 'Снять подтверждение' : 'Подтвердить профиль' }}
        </button>
        <form v-if="user.isRoot" class="flex items-end gap-space-sm" @submit.prevent="grant">
          <div class="min-w-0 flex-1">
            <FormSelect v-model="grantRole" label="Роль" :options="roleOptions" />
          </div>
          <button
            type="submit"
            class="mb-0.5 flex shrink-0 items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
            :disabled="!grantRole || acting"
          >
            <MsIcon name="key" :size="18" />
            Выдать
          </button>
        </form>
      </div>

      <InlineNotice v-if="toolError" tone="error">{{ toolError }}</InlineNotice>
      <InlineNotice v-else-if="toolNotice" tone="success">{{ toolNotice }}</InlineNotice>
    </div>
  </section>
</template>
