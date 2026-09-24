<script setup lang="ts">
import { computed, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import { can, type SessionUser, type UserRole } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'

import { EVERYONE_CAN, ROLES, ROLE_ORDER, fetchProfileById, verifyProfile, type Profile } from '../data'

/**
 * Роль и что она даёт.
 *
 * Саму роль выдаёт только администратор платформы — в приложении её не
 * назначить и не снять; заявка на краеведа и поисковика живёт в соседней
 * карточке. Здесь остаётся подтверждение профиля по жетону: краевед и
 * модератор ручаются за человека, которого видели (`_VERIFIER_ROLES` в
 * user_service).
 */
const props = defineProps<{ user: SessionUser }>()

const emit = defineEmits<{ 'open-token': [] }>()

const role = computed(() => props.user.role ?? 'family')
const canVerify = computed(() => can.verifyProfile(props.user))
const othersOpen = ref(false)

// --- краевед и модератор подтверждают исследователя по номеру жетона ---

const tokenId = ref('')
const found = ref<Profile | null>(null)
const looking = ref(false)
const acting = ref(false)
const toolError = ref<string | null>(null)
const toolNotice = ref<string | null>(null)

const tokenValid = computed(() => /^[0-9a-f-]{8,36}$/i.test(tokenId.value.trim()))

async function lookUp(): Promise<void> {
  if (!tokenValid.value || looking.value) return
  looking.value = true
  toolError.value = null
  toolNotice.value = null
  found.value = null
  try {
    found.value = await fetchProfileById(tokenId.value.trim())
  } catch (reason) {
    toolError.value =
      reason instanceof ApiError && reason.status === 404 ? 'Исследователь с таким жетоном не найден' : errorText(reason)
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
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">Доступ</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">Роль и что она даёт</h2>
    </div>

    <div class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div class="flex items-center gap-space-sm">
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
          aria-hidden="true"
        >
          <MsIcon :name="ROLES[role].icon" :size="20" filled />
        </span>
        <div class="min-w-0">
          <p class="font-archival text-archival uppercase text-on-surface-variant">Ваша роль</p>
          <p class="font-headline-sm text-headline-sm text-on-surface">{{ ROLES[role].title }}</p>
        </div>
      </div>
      <ul class="flex flex-col gap-1">
        <li
          v-for="item in [...ROLES[role].gives, ...EVERYONE_CAN]"
          :key="item"
          class="flex items-start gap-space-xs font-body-sm text-body-sm text-on-surface"
        >
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
          <li
            v-for="other in ROLE_ORDER.filter((value) => value !== role && ROLES[value].gives.length)"
            :key="other"
            class="flex items-start gap-space-sm"
          >
            <MsIcon :name="ROLES[other].icon" :size="18" class="mt-0.5 shrink-0 text-on-surface-variant" />
            <div class="min-w-0">
              <p class="font-label-md text-label-md text-on-surface">{{ ROLES[other].title }}</p>
              <p class="font-body-sm text-body-sm text-on-surface-variant">{{ ROLES[other].gives.join(' · ') }}</p>
            </div>
          </li>
        </ul>
      </div>

      <!-- Жетон нужен любому: по его номеру краевед подтверждает человека, которого видел. -->
      <button
        type="button"
        class="flex items-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
        @click="emit('open-token')"
      >
        <MsIcon name="badge" :size="18" />
        Мой жетон исследователя
      </button>
    </div>

    <!-- Краевед и модератор: подтвердить исследователя по жетону. -->
    <div v-if="canVerify" class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div class="flex items-start gap-space-sm">
        <span
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed"
          aria-hidden="true"
        >
          <MsIcon name="how_to_reg" :size="20" />
        </span>
        <div class="min-w-0">
          <p class="font-archival text-archival uppercase text-on-surface-variant">По жетону исследователя</p>
          <p class="font-headline-sm text-headline-sm text-on-surface">Подтвердить исследователя</p>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Попросите номер жетона — человек откроет его в своём профиле кнопкой «Мой жетон исследователя». Роль этим не
            выдаётся: её назначает администратор платформы.
          </p>
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
          <MsIcon
            :name="found.is_verified ? 'verified' : 'person'"
            :size="20"
            :filled="found.is_verified"
            :class="found.is_verified ? 'text-tertiary' : 'text-on-surface-variant'"
          />
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
      </div>

      <InlineNotice v-if="toolError" tone="error">{{ toolError }}</InlineNotice>
      <InlineNotice v-else-if="toolNotice" tone="success">{{ toolNotice }}</InlineNotice>
    </div>
  </section>
</template>
