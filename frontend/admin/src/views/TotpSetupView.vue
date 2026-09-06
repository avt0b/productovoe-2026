<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { authApi } from '@/api/endpoints'
import { errorText } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const secret = ref('')
const otpauthUri = ref('')
const code = ref('')
const codes = ref<string[]>([])
const loading = ref(true)
const submitting = ref(false)
const error = ref<string | null>(null)
const copied = ref(false)

/** Секрет читают глазами и вбивают руками — группы по четыре символа. */
const readableSecret = computed(() => (secret.value.match(/.{1,4}/g) ?? []).join(' '))
const done = computed(() => codes.value.length > 0)

onMounted(async () => {
  try {
    const setup = await authApi.totpSetup()
    secret.value = setup.secret
    otpauthUri.value = setup.otpauth_uri
  } catch (e) {
    error.value = errorText(e)
  } finally {
    loading.value = false
  }
})

async function copySecret(): Promise<void> {
  try {
    await navigator.clipboard.writeText(secret.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    error.value = 'Не удалось скопировать — выделите ключ вручную'
  }
}

async function confirm(): Promise<void> {
  error.value = null
  submitting.value = true
  try {
    const result = await authApi.totpConfirm(code.value.trim())
    codes.value = result.codes
    await auth.fetchMe()
  } catch (e) {
    error.value = errorText(e)
  } finally {
    submitting.value = false
  }
}

function downloadCodes(): void {
  const text = [
    'Коды восстановления — панель администратора «Маршруты победы»',
    `Учётная запись: ${auth.me?.email ?? ''}`,
    'Каждый код срабатывает один раз. Храните в надёжном месте.',
    '',
    ...codes.value,
  ].join('\n')

  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'marshruty-recovery-codes.txt'
  link.click()
  URL.revokeObjectURL(url)
}

async function finish(): Promise<void> {
  await router.push({ name: 'dashboard' })
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background p-space-4">
    <div class="w-full max-w-2xl">
      <div class="mb-space-6 flex flex-col gap-space-1 text-center">
        <span
          class="font-label-archive-code text-label-archive-code uppercase tracking-widest text-primary"
        >
          Обязательный шаг
        </span>
        <h1 class="font-headline-md text-headline-md uppercase tracking-wide text-on-surface">
          Настройка двухфакторной аутентификации
        </h1>
        <p class="font-body-md text-body-md text-on-surface-variant">
          Пока второй фактор не настроен, остальные разделы панели закрыты.
        </p>
      </div>

      <div class="rounded-xl bg-surface-container-lowest p-space-6 shadow-sm">
        <div v-if="loading" class="h-40 animate-pulse rounded-lg bg-surface-container" />

        <!-- Шаг 1: ключ и подтверждение -->
        <div v-else-if="!done" class="flex flex-col gap-space-5">
          <ol class="flex flex-col gap-space-4">
            <li class="flex gap-space-3">
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary font-label-action text-label-action text-on-primary"
              >
                1
              </span>
              <div class="flex flex-col gap-space-2">
                <span class="font-label-action text-label-action uppercase text-on-surface">
                  Установите приложение-аутентификатор
                </span>
                <span class="font-body-sm text-body-sm text-on-surface-variant">
                  Google Authenticator, Aegis, 1Password — подойдёт любое с поддержкой TOTP.
                </span>
              </div>
            </li>

            <li class="flex gap-space-3">
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary font-label-action text-label-action text-on-primary"
              >
                2
              </span>
              <div class="flex w-full flex-col gap-space-2">
                <span class="font-label-action text-label-action uppercase text-on-surface">
                  Добавьте учётную запись по ключу
                </span>
                <div class="rounded-lg bg-surface-container p-space-4">
                  <span class="field-label">Ключ настройки</span>
                  <div class="flex items-center justify-between gap-space-3">
                    <code class="font-label-coordinate text-[15px] tracking-widest text-primary">
                      {{ readableSecret }}
                    </code>
                    <button class="btn-secondary btn-sm" type="button" @click="copySecret">
                      <span class="ms-icon text-[16px]">
                        {{ copied ? 'check' : 'content_copy' }}
                      </span>
                      {{ copied ? 'Скопирован' : 'Копировать' }}
                    </button>
                  </div>
                  <p class="mt-space-2 font-body-sm text-body-sm text-on-surface-variant">
                    Тип — «по времени» (TOTP), имя учётной записи — {{ auth.me?.email }}.
                  </p>
                  <details class="mt-space-2">
                    <summary
                      class="cursor-pointer font-label-archive-code text-label-archive-code uppercase text-secondary"
                    >
                      Ссылка otpauth:// для менеджеров паролей
                    </summary>
                    <code
                      class="mt-space-1 block break-all font-label-archive-code text-label-archive-code text-on-surface-variant"
                    >
                      {{ otpauthUri }}
                    </code>
                  </details>
                </div>
              </div>
            </li>

            <li class="flex gap-space-3">
              <span
                class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary font-label-action text-label-action text-on-primary"
              >
                3
              </span>
              <div class="flex w-full flex-col gap-space-2">
                <label class="font-label-action text-label-action uppercase text-on-surface" for="code">
                  Введите код из приложения
                </label>
                <input
                  id="code"
                  v-model="code"
                  class="field max-w-[220px] text-center font-headline-md text-headline-md tracking-[0.3em] text-primary"
                  type="text"
                  inputmode="numeric"
                  maxlength="6"
                  placeholder="000000"
                  autocomplete="one-time-code"
                  @keyup.enter="confirm"
                />
              </div>
            </li>
          </ol>

          <p
            v-if="error"
            class="rounded-lg bg-error-container px-space-3 py-space-2 font-body-sm text-body-sm text-on-error-container"
            role="alert"
          >
            {{ error }}
          </p>

          <button
            class="btn-primary w-full"
            type="button"
            :disabled="submitting || code.trim().length < 6"
            @click="confirm"
          >
            <span class="ms-icon text-[18px]">verified_user</span>
            {{ submitting ? 'Проверяем…' : 'Включить двухфакторную аутентификацию' }}
          </button>
        </div>

        <!-- Шаг 2: коды восстановления -->
        <div v-else class="flex flex-col gap-space-4">
          <div class="flex items-center gap-space-2 text-verified">
            <span class="ms-icon text-[24px]">check_circle</span>
            <span class="font-headline-sm text-headline-sm uppercase">
              Двухфакторная аутентификация включена
            </span>
          </div>

          <div class="rounded-lg bg-tertiary-fixed p-space-4 text-on-tertiary-fixed">
            <p class="font-label-action text-label-action uppercase">
              Сохраните коды восстановления
            </p>
            <p class="mt-space-1 font-body-sm text-body-sm">
              Они показываются один раз и понадобятся, если телефон будет потерян. Каждый код
              срабатывает однократно.
            </p>
          </div>

          <div class="grid grid-cols-2 gap-space-2 rounded-lg bg-surface-container p-space-4">
            <code
              v-for="item in codes"
              :key="item"
              class="font-label-coordinate text-[14px] tracking-widest text-on-surface"
            >
              {{ item }}
            </code>
          </div>

          <div class="flex flex-wrap items-center gap-space-3">
            <button class="btn-secondary" type="button" @click="downloadCodes">
              <span class="ms-icon text-[18px]">download</span>
              Скачать файлом
            </button>
            <button class="btn-primary flex-1" type="button" @click="finish">
              Я сохранил коды — перейти в панель
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
