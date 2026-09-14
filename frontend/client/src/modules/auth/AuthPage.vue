<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorText } from '@/core/format'
import { usePreferencesStore } from '@/core/preferences'
import { useSessionStore, type SignInMethod } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'

import AuthBanner from './components/AuthBanner.vue'
import AuthField from './components/AuthField.vue'
import SsoButtons from './components/SsoButtons.vue'

type Mode = 'login' | 'register'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const preferences = usePreferencesStore()

const mode = ref<Mode>('login')
const name = ref('')
const contact = ref('')
const password = ref('')
const passwordVisible = ref(false)
/** Регистрируется краевед или наставник — он сможет водить экскурсии и собирать группу бампом. */
const isGuide = ref(false)
const signInError = ref<string | null>(null)
/** Какой способ входа сейчас в работе — чтобы крутилка была на нажатой кнопке, а не на всех. */
const activeMethod = ref<SignInMethod | null>(null)

const submitLabel = computed(() => (mode.value === 'login' ? 'Войти в экспедицию' : 'Создать аккаунт'))

/**
 * Куда вернуть после входа. Только внутренний путь: `?next=//evil.example`
 * иначе увёл бы человека на чужой сайт прямо с экрана входа.
 */
function nextPath(): string | null {
  const next = route.query.next
  return typeof next === 'string' && next.startsWith('/') && !next.startsWith('//') ? next : null
}

async function enter(method: SignInMethod): Promise<void> {
  if (session.pending) return
  activeMethod.value = method
  signInError.value = null
  try {
    await session.signIn({
      method,
      contact: contact.value,
      password: password.value,
      name: mode.value === 'register' ? name.value : undefined,
      role: mode.value === 'register' && isGuide.value ? 'local_historian' : undefined,
    })
    await router.replace(nextPath() ?? { name: 'home' })
  } catch (reason) {
    signInError.value = errorText(reason)
  } finally {
    activeMethod.value = null
  }
}

function submit(): void {
  void enter(mode.value === 'login' ? 'password' : 'register')
}
</script>

<template>
  <div class="flex w-full flex-col px-margin pb-space-xl">
    <!-- Эмблема и название -->
    <div class="mb-space-md mt-space-sm flex flex-col items-center text-center">
      <div class="relative mb-space-sm flex items-center justify-center">
        <div class="flex h-20 w-20 items-center justify-center rounded-full bg-secondary-container p-1 shadow-md">
          <img src="/logo.svg" alt="Эмблема «Маршруты победы»" class="h-full w-full rounded-full object-contain" />
        </div>
        <div
          class="absolute -bottom-1 -right-1 flex items-center justify-center rounded-full bg-primary p-1 text-on-primary shadow-sm"
        >
          <MsIcon name="explore" :size="13" />
        </div>
      </div>
      <h1 class="font-headline-xl-mobile text-headline-xl-mobile tracking-tight text-on-surface">Маршруты победы</h1>
      <p class="mt-space-xs max-w-xs font-body-sm text-body-sm text-on-surface-variant">
        Живая история, семейные маршруты и поиск защитников Отечества
      </p>
    </div>

    <AuthBanner class="mb-space-lg" />

    <div class="flex w-full flex-col rounded-2xl bg-surface-container-lowest p-space-md shadow-sm">
      <!-- Вход / Регистрация -->
      <div class="mb-space-lg grid grid-cols-2 rounded-full bg-surface-container-low p-1 text-center" role="tablist">
        <button
          v-for="tab in [
            { value: 'login', title: 'Вход' },
            { value: 'register', title: 'Регистрация' },
          ] as const"
          :key="tab.value"
          type="button"
          role="tab"
          :aria-selected="mode === tab.value"
          class="rounded-full py-2 font-label-lg text-label-lg transition-all duration-200"
          :class="
            mode === tab.value
              ? 'bg-surface-container-lowest text-on-surface shadow-sm'
              : 'text-on-surface-variant hover:text-on-surface'
          "
          @click="mode = tab.value"
        >
          {{ tab.title }}
        </button>
      </div>

      <form class="flex flex-col space-y-space-md" @submit.prevent="submit">
        <AuthField
          v-if="mode === 'register'"
          v-model="name"
          label="Как к вам обращаться"
          icon="person"
          placeholder="Имя и фамилия"
          autocomplete="name"
        />

        <AuthField
          v-model="contact"
          label="Почта"
          icon="mail"
          type="email"
          placeholder="name@mail.ru"
          autocomplete="username"
        />

        <AuthField
          v-model="password"
          label="Пароль"
          icon="lock"
          :type="passwordVisible ? 'text' : 'password'"
          :placeholder="mode === 'login' ? 'Введите ваш пароль' : 'Не короче 8 символов'"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
        >
          <template v-if="mode === 'login'" #label-action>
            <button type="button" class="font-label-sm text-label-sm text-primary transition-colors hover:text-primary-container">
              Забыли пароль?
            </button>
          </template>
          <template #trailing>
            <button
              type="button"
              class="flex shrink-0 items-center p-1 text-outline hover:text-on-surface"
              :aria-label="passwordVisible ? 'Скрыть пароль' : 'Показать пароль'"
              @click="passwordVisible = !passwordVisible"
            >
              <MsIcon :name="passwordVisible ? 'visibility_off' : 'visibility'" :size="18" />
            </button>
          </template>
        </AuthField>

        <!-- Краевед при регистрации: сможет водить экскурсии и собирать группу бампом -->
        <div v-if="mode === 'register'" class="flex items-center justify-between rounded-xl bg-surface-container-low p-space-sm">
          <div class="flex items-center space-x-space-sm">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary-fixed text-secondary">
              <MsIcon name="record_voice_over" :size="15" />
            </div>
            <div class="flex flex-col">
              <span class="font-label-md text-label-md text-on-surface">Я краевед или наставник</span>
              <span class="font-label-sm text-label-sm text-on-surface-variant">Буду водить экскурсии и собирать группы</span>
            </div>
          </div>
          <ToggleSwitch v-model="isGuide" label="Я краевед или наставник" class="ml-2" />
        </div>

        <!-- Семейный режим -->
        <div class="flex items-center justify-between rounded-xl bg-surface-container-low p-space-sm">
          <div class="flex items-center space-x-space-sm">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed">
              <MsIcon name="family_restroom" :size="15" filled />
            </div>
            <div class="flex flex-col">
              <span class="font-label-md text-label-md text-on-surface">Семейный / детский режим</span>
              <span class="font-label-sm text-label-sm text-on-surface-variant">Адаптированные детские квесты и аудиогид</span>
            </div>
          </div>
          <ToggleSwitch v-model="preferences.familyMode" label="Семейный режим" class="ml-2" />
        </div>

        <button
          type="submit"
          class="flex w-full items-center justify-center space-x-space-sm rounded-full bg-primary py-4 font-label-lg text-label-lg text-on-primary shadow-md transition-all hover:bg-primary-container active:scale-[0.99] disabled:opacity-70"
          :disabled="session.pending"
        >
          <MsIcon
            :name="activeMethod === 'password' || activeMethod === 'register' ? 'progress_activity' : 'military_tech'"
            :size="18"
            :class="{ 'animate-spin': activeMethod === 'password' || activeMethod === 'register' }"
          />
          <span>{{ submitLabel }}</span>
        </button>

        <p
          v-if="signInError"
          class="rounded-xl bg-error-container px-space-sm py-2 text-center font-body-sm text-body-sm text-on-error-container"
          role="alert"
        >
          {{ signInError }}
        </p>

        <p class="text-center font-label-sm text-label-sm text-outline">
          Оставьте поля пустыми, чтобы войти в демо-режиме без аккаунта. Записаться на экскурсию в нём нельзя.
        </p>
      </form>

      <div class="relative flex items-center justify-center py-space-md">
        <div class="h-px flex-grow bg-surface-variant" />
        <span class="mx-space-sm shrink-0 font-label-sm text-label-sm text-outline">Или войти через</span>
        <div class="h-px flex-grow bg-surface-variant" />
      </div>

      <SsoButtons :active="activeMethod" :disabled="session.pending" class="mb-space-sm" @select="enter" />
    </div>

    <!-- Архивная полоска -->
    <div class="mt-space-lg flex items-center space-x-space-sm rounded-xl bg-surface-container-low p-space-sm">
      <div class="h-12 w-12 shrink-0 overflow-hidden rounded-lg bg-surface-dim">
        <img
          class="h-full w-full object-cover"
          alt=""
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuAHhZ45eCVlfWovdLW6mY6zekfNfLjW7ajfrwPq5RHq9QANzd5Q4UwMDLkSAK-uRY1NcXfys9MarUjZo1yAO6ajFraO2WMNkWuKAGKSpJ_JhuwJ3INnwx24y8nosH3hUKZ0Go7OXsJMhNql6bZCwLhXYgIWYr2Y-IwW4y5gN8wFP5KKUbs925lJDgQ8ANBanWxuPT684JefTt454Ib1AFPQ_MagPSVEfrSm3evqHE8DgfCvq0Hs9xoA"
        />
      </div>
      <div class="flex min-w-0 flex-1 flex-col">
        <span class="font-label-md text-label-md text-on-surface">Более 14 000 архивных карточек</span>
        <span class="truncate font-body-sm text-body-sm text-on-surface-variant">
          Оцифрованные маршруты боевого пути и наградные листы
        </span>
      </div>
    </div>

    <div class="mt-space-lg px-space-sm text-center">
      <p class="font-label-sm text-label-sm text-outline">
        Нажимая «Войти», вы соглашаетесь с
        <a class="underline transition-colors hover:text-on-surface" href="#">Политикой памяти</a>
        и правилами обработки персональных данных.
      </p>
    </div>
  </div>
</template>
