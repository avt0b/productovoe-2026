<script setup lang="ts">
import type { ComponentPublicInstance } from 'vue'
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorText } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref<string | null>(null)

/** Шесть отдельных полей под код — как в макете. */
const digits = ref<string[]>(['', '', '', '', '', ''])
const digitRefs = ref<HTMLInputElement[]>([])
const recoveryMode = ref(false)
const recoveryCode = ref('')

const step = computed<'password' | 'mfa'>(() => (auth.mfaToken ? 'mfa' : 'password'))
const code = computed(() => digits.value.join(''))

watch(step, async (value) => {
  if (value === 'mfa') {
    await nextTick()
    digitRefs.value[0]?.focus()
  }
})

async function submitPassword(): Promise<void> {
  error.value = null
  try {
    const needsMfa = await auth.login(email.value.trim(), password.value)
    if (!needsMfa) await goNext()
  } catch (e) {
    error.value = errorText(e)
  }
}

async function submitMfa(): Promise<void> {
  error.value = null
  const value = recoveryMode.value ? recoveryCode.value.trim() : code.value
  if (!value) {
    error.value = 'Введите код подтверждения'
    return
  }
  try {
    await auth.submitMfa(value)
    await goNext()
  } catch (e) {
    error.value = errorText(e)
    digits.value = ['', '', '', '', '', '']
    await nextTick()
    digitRefs.value[0]?.focus()
  }
}

async function goNext(): Promise<void> {
  const next = typeof route.query.next === 'string' ? route.query.next : '/'
  await router.push(auth.needsTotpSetup ? { name: 'totp-setup' } : next)
}

/** Собираем ссылки на поля кода, чтобы переводить фокус между ними. */
function setDigitRef(el: Element | ComponentPublicInstance | null, index: number): void {
  if (el instanceof HTMLInputElement) digitRefs.value[index] = el
}

function onDigit(index: number, event: Event): void {
  const input = event.target as HTMLInputElement
  const value = input.value.replace(/\D/g, '')

  if (value.length > 1) {
    // Вставка кода целиком из буфера обмена.
    const chars = value.slice(0, 6).split('')
    digits.value = Array.from({ length: 6 }, (_, i) => chars[i] ?? '')
    digitRefs.value[Math.min(chars.length, 5)]?.focus()
    return
  }

  digits.value[index] = value
  if (value && index < 5) digitRefs.value[index + 1]?.focus()
  if (index === 5 && digits.value.every(Boolean)) void submitMfa()
}

function onDigitBackspace(index: number): void {
  if (!digits.value[index] && index > 0) digitRefs.value[index - 1]?.focus()
}

function backToPassword(): void {
  auth.cancelMfa()
  password.value = ''
  digits.value = ['', '', '', '', '', '']
  recoveryMode.value = false
  recoveryCode.value = ''
  error.value = null
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background p-space-4">
    <div class="w-full max-w-md">
      <div class="mb-space-6 flex flex-col items-center gap-space-2 text-center">
        <svg class="h-12 w-12" viewBox="0 0 32 32" aria-hidden="true">
          <circle cx="16" cy="16" r="15" fill="none" stroke="#495d38" stroke-width="1.5" />
          <path
            d="M16 6l2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-3-5.3 3 1.1-6-4.4-4.2 6-.8z"
            fill="#495d38"
          />
        </svg>
        <h1 class="font-headline-md text-headline-md uppercase tracking-wide text-primary">
          Маршруты победы
        </h1>
        <p
          class="font-label-archive-code text-label-archive-code uppercase tracking-wider text-on-surface-variant"
        >
          Служебный вход в панель администратора
        </p>
      </div>

      <div class="rounded-xl bg-surface-container-lowest p-space-6 shadow-sm">
        <!-- Шаг 1 -->
        <form v-if="step === 'password'" class="flex flex-col gap-space-4" @submit.prevent="submitPassword">
          <div>
            <label class="field-label" for="email">Служебная почта</label>
            <input
              id="email"
              v-model="email"
              class="field"
              type="email"
              autocomplete="username"
              required
              placeholder="admin@marshruty.ru"
            />
          </div>

          <div>
            <label class="field-label" for="password">Пароль</label>
            <div class="relative">
              <input
                id="password"
                v-model="password"
                class="field pr-10"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                placeholder="••••••••••"
              />
              <button
                class="absolute right-space-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
                type="button"
                :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
                @click="showPassword = !showPassword"
              >
                <span class="ms-icon text-[20px]">
                  {{ showPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </div>

          <p
            v-if="error"
            class="rounded-lg bg-error-container px-space-3 py-space-2 font-body-sm text-body-sm text-on-error-container"
            role="alert"
          >
            {{ error }}
          </p>

          <button class="btn-primary w-full" type="submit" :disabled="auth.loading">
            <span class="ms-icon text-[18px]">login</span>
            {{ auth.loading ? 'Проверяем…' : 'Войти' }}
          </button>
        </form>

        <!-- Шаг 2 -->
        <form v-else class="flex flex-col gap-space-4" @submit.prevent="submitMfa">
          <div class="flex flex-col gap-space-1">
            <span class="font-headline-sm text-headline-sm uppercase text-on-surface">
              Подтверждение входа
            </span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">
              {{
                recoveryMode
                  ? 'Введите один из сохранённых кодов восстановления.'
                  : 'Введите шестизначный код из приложения-аутентификатора.'
              }}
            </span>
          </div>

          <div v-if="!recoveryMode" class="grid grid-cols-6 gap-space-2">
            <input
              v-for="(digit, index) in digits"
              :key="index"
              :ref="(el) => setDigitRef(el, index)"
              :value="digit"
              class="h-12 rounded-lg bg-surface-container text-center font-headline-md text-headline-md text-primary focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-primary"
              type="text"
              inputmode="numeric"
              maxlength="6"
              autocomplete="one-time-code"
              :aria-label="`Цифра ${index + 1}`"
              @input="onDigit(index, $event)"
              @keydown.backspace="onDigitBackspace(index)"
            />
          </div>

          <div v-else>
            <label class="field-label" for="recovery">Код восстановления</label>
            <input
              id="recovery"
              v-model="recoveryCode"
              class="field font-label-coordinate uppercase"
              type="text"
              placeholder="ABCD-EF23"
              autocomplete="off"
            />
          </div>

          <p
            v-if="error"
            class="rounded-lg bg-error-container px-space-3 py-space-2 font-body-sm text-body-sm text-on-error-container"
            role="alert"
          >
            {{ error }}
          </p>

          <button class="btn-primary w-full" type="submit" :disabled="auth.loading">
            <span class="ms-icon text-[18px]">verified_user</span>
            {{ auth.loading ? 'Проверяем…' : 'Подтвердить' }}
          </button>

          <div class="flex items-center justify-between">
            <button
              class="font-label-action text-label-action uppercase text-secondary hover:underline"
              type="button"
              @click="recoveryMode = !recoveryMode"
            >
              {{ recoveryMode ? 'Ввести код из приложения' : 'Использовать код восстановления' }}
            </button>
            <button
              class="font-label-action text-label-action uppercase text-on-surface-variant hover:underline"
              type="button"
              @click="backToPassword"
            >
              Назад
            </button>
          </div>
        </form>
      </div>

      <p class="mt-space-4 text-center font-body-sm text-body-sm text-on-surface-variant">
        Доступ к персональным данным погибших журналируется.
      </p>
    </div>
  </div>
</template>
