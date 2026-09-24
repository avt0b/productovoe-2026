<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { errorText, formatDate } from '@/core/format'
import { shareText } from '@/core/share'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'

import {
  createFamilyInvite,
  familyMembers,
  redeemFamilyInvite,
  removeFamilyMember,
  type FamilyInvite,
  type FamilyMember,
} from '../data'

/**
 * Семья на платформе: родитель и ребёнок, бабушка и внук — те, кто ходит по
 * маршрутам вместе и хочет видеть друг друга в приложении.
 *
 * Связь заводится коротким кодом: один человек его выпускает, второй вводит.
 * Код одноразовый и живёт неделю (`FamilyLinkService` в user_service), поэтому
 * показываем и срок — иначе человек не поймёт, почему код перестал работать.
 */
const members = ref<FamilyMember[]>([])
const loading = ref(true)
const invite = ref<FamilyInvite | null>(null)
const inviting = ref(false)
const shared = ref(false)

const code = ref('')
const joining = ref(false)
const entering = ref(false)

const busyMember = ref<string | null>(null)
const confirmingRemove = ref<string | null>(null)

const error = ref<string | null>(null)
const notice = ref<string | null>(null)

/** Код набирают руками с чужого экрана: восемь знаков без похожих букв. */
const codeValid = computed(() => code.value.trim().length === 8)

async function load(): Promise<void> {
  try {
    members.value = await familyMembers()
    error.value = null
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function makeInvite(): Promise<void> {
  if (inviting.value) return
  inviting.value = true
  error.value = null
  notice.value = null
  try {
    invite.value = await createFamilyInvite()
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    inviting.value = false
  }
}

async function passCode(): Promise<void> {
  const current = invite.value
  if (!current) return
  const outcome = await shareText('Код для семьи в «Маршрутах победы»', current.code)
  shared.value = outcome !== 'failed'
  if (outcome === 'failed') error.value = 'Передать код не вышло — продиктуйте его или перепишите с экрана'
}

async function join(): Promise<void> {
  if (!codeValid.value || joining.value) return
  joining.value = true
  error.value = null
  notice.value = null
  try {
    await redeemFamilyInvite(code.value)
    code.value = ''
    entering.value = false
    notice.value = 'Готово — вы в одной семье'
    await load()
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    joining.value = false
  }
}

async function remove(member: FamilyMember): Promise<void> {
  if (busyMember.value) return
  busyMember.value = member.member_id
  error.value = null
  notice.value = null
  try {
    await removeFamilyMember(member.member_id)
    confirmingRemove.value = null
    notice.value = 'Связь разорвана с обеих сторон'
    await load()
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    busyMember.value = null
  }
}

function nameOf(member: FamilyMember): string {
  return member.display_name || 'Участник платформы'
}
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">Кто рядом</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">Моя семья</h2>
    </div>

    <div class="flex flex-col gap-space-md rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <p class="font-body-sm text-body-sm text-on-surface-variant">
        Свяжите учётные записи с теми, с кем ходите по маршрутам: родителем, ребёнком, бабушкой. Это не «Герои семьи» —
        там древо памяти, а здесь живые люди в приложении.
      </p>

      <div v-if="loading" class="flex items-center gap-space-xs font-label-md text-label-md text-on-surface-variant" role="status">
        <MsIcon name="progress_activity" :size="18" class="animate-spin" />
        Смотрим, кто уже в семье…
      </div>

      <ul v-else-if="members.length" class="flex flex-col gap-space-xs">
        <li v-for="member in members" :key="member.member_id" class="flex flex-col gap-space-xs">
          <div class="flex items-center gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
            <span
              class="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full bg-surface-container-high text-on-surface-variant"
              aria-hidden="true"
            >
              <img v-if="member.avatar_url" :src="member.avatar_url" alt="" class="h-full w-full object-cover" loading="lazy" />
              <MsIcon v-else name="person" :size="20" />
            </span>
            <div class="flex min-w-0 flex-1 flex-col">
              <span class="truncate font-label-lg text-label-lg text-on-surface">{{ nameOf(member) }}</span>
              <span class="truncate font-body-sm text-body-sm text-on-surface-variant">
                {{ [member.city, `в семье с ${formatDate(member.linked_at)}`].filter(Boolean).join(' · ') }}
              </span>
            </div>
            <button
              type="button"
              :aria-label="`Убрать из семьи: ${nameOf(member)}`"
              :aria-expanded="confirmingRemove === member.member_id"
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface active:scale-95"
              @click="confirmingRemove = confirmingRemove === member.member_id ? null : member.member_id"
            >
              <MsIcon name="link_off" :size="18" />
            </button>
          </div>

          <!-- Подтверждение раскрывается высотой: список не прыгает. -->
          <div
            class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
            :class="confirmingRemove === member.member_id ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
            :inert="confirmingRemove !== member.member_id"
          >
            <div class="overflow-hidden">
              <div class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-low p-space-md" role="alertdialog">
                <p class="font-body-sm text-body-sm text-on-surface">
                  Разорвать связь с «{{ nameOf(member) }}»? Вы пропадёте из семьи друг у друга.
                </p>
                <div class="flex gap-space-sm">
                  <button
                    type="button"
                    class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
                    @click="confirmingRemove = null"
                  >
                    Оставить
                  </button>
                  <button
                    type="button"
                    class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error active:scale-95 disabled:opacity-60"
                    :disabled="busyMember === member.member_id"
                    @click="remove(member)"
                  >
                    <MsIcon name="link_off" :size="18" />
                    Разорвать
                  </button>
                </div>
              </div>
            </div>
          </div>
        </li>
      </ul>

      <p v-else class="rounded-2xl bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
        Пока никого. Выпустите код и передайте его своим — или введите код, который дали вам.
      </p>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <InlineNotice v-else-if="notice" tone="success">{{ notice }}</InlineNotice>

      <!-- Выпущенный код: показываем целиком, его диктуют и переписывают. -->
      <div v-if="invite" class="flex flex-col items-center gap-space-xs rounded-2xl bg-surface-container-low p-space-md">
        <span class="font-archival text-archival uppercase text-on-surface-variant">Код для своих</span>
        <span class="select-all font-headline-md text-headline-md tracking-[0.2em] text-on-surface">{{ invite.code }}</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Одно использование, действует до {{ formatDate(invite.expires_at) }}
        </span>
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="passCode"
        >
          <MsIcon :name="shared ? 'check' : 'share'" :size="18" />
          {{ shared ? 'Код передан' : 'Передать код' }}
        </button>
      </div>

      <div class="flex flex-wrap gap-space-xs">
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
          :disabled="inviting"
          @click="makeInvite"
        >
          <MsIcon :name="inviting ? 'progress_activity' : 'key'" :size="18" :class="{ 'animate-spin': inviting }" />
          {{ invite ? 'Новый код' : 'Пригласить в семью' }}
        </button>
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          :aria-expanded="entering"
          @click="entering = !entering"
        >
          <MsIcon :name="entering ? 'close' : 'group_add'" :size="18" />
          {{ entering ? 'Отменить' : 'У меня есть код' }}
        </button>
      </div>

      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="entering ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!entering"
      >
        <form class="flex flex-col gap-space-sm overflow-hidden" @submit.prevent="join">
          <div class="pt-space-xs">
            <FormInput
              v-model="code"
              label="Код из восьми знаков"
              icon="key"
              :maxlength="8"
              placeholder="K7M2QX4A"
              hint="Тот, кто вас приглашает, выпускает код у себя в профиле"
            />
          </div>
          <button
            type="submit"
            class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
            :disabled="!codeValid || joining"
          >
            <MsIcon :name="joining ? 'progress_activity' : 'group_add'" :size="18" :class="{ 'animate-spin': joining }" />
            <span>Войти в семью</span>
          </button>
        </form>
      </div>
    </div>
  </section>
</template>
