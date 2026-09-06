<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { authApi } from '@/api/endpoints'
import ModalDialog from '@/components/ModalDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { errorText, formatDateTime } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const busy = ref(false)
const message = ref<string | null>(null)
const error = ref<string | null>(null)

// --- смена пароля ---
const showPasswordForm = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const repeatPassword = ref('')

async function changePassword(): Promise<void> {
  error.value = null
  if (newPassword.value !== repeatPassword.value) {
    error.value = 'Новый пароль и подтверждение не совпадают'
    return
  }
  busy.value = true
  try {
    await authApi.changePassword(currentPassword.value, newPassword.value)
    // Смена пароля гасит все сессии, включая текущую — уводим на вход.
    await auth.logout()
    await router.push({ name: 'login' })
  } catch (e) {
    error.value = errorText(e)
  } finally {
    busy.value = false
  }
}

// --- перевыпуск кодов восстановления ---
const showCodesForm = ref(false)
const totpCode = ref('')
const newCodes = ref<string[]>([])

async function regenerate(): Promise<void> {
  error.value = null
  busy.value = true
  try {
    const result = await authApi.regenerateRecoveryCodes(totpCode.value.trim())
    newCodes.value = result.codes
    totpCode.value = ''
    await auth.fetchMe()
    message.value = 'Коды перевыпущены. Прежние больше не действуют.'
  } catch (e) {
    error.value = errorText(e)
  } finally {
    busy.value = false
  }
}

function openCodesForm(): void {
  showCodesForm.value = true
  newCodes.value = []
  totpCode.value = ''
  error.value = null
}

/** Гасит сессии на всех устройствах — в том числе текущую. */
async function logoutEverywhere(): Promise<void> {
  busy.value = true
  error.value = null
  try {
    await authApi.logoutEverywhere()
    await auth.logout()
    await router.push({ name: 'login' })
  } catch (e) {
    error.value = errorText(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-space-6">
    <PageHeader
      eyebrow="Моя учётная запись"
      title="Безопасность"
      subtitle="Второй фактор, пароль и коды восстановления."
    />

    <p
      v-if="message"
      class="rounded-lg bg-verified-container px-space-4 py-space-3 font-body-sm text-body-sm text-verified"
    >
      {{ message }}
    </p>
    <p
      v-if="error"
      class="rounded-lg bg-error-container px-space-4 py-space-3 font-body-sm text-body-sm text-on-error-container"
      role="alert"
    >
      {{ error }}
    </p>

    <div class="grid grid-cols-1 gap-card-gap lg:grid-cols-2">
      <!-- Профиль -->
      <section class="card flex flex-col gap-space-3">
        <h2 class="font-headline-sm text-headline-sm uppercase text-on-surface">Учётная запись</h2>
        <div class="flex flex-col gap-space-2">
          <div class="flex items-center justify-between">
            <span class="field-label mb-0">Почта</span>
            <span class="font-body-md text-body-md text-on-surface">{{ auth.me?.email }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="field-label mb-0">Роль</span>
            <span class="font-body-md text-body-md text-on-surface">{{ auth.me?.role }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="field-label mb-0">Последний вход</span>
            <span class="mono text-on-surface-variant">
              {{ auth.me?.last_login_at ? formatDateTime(auth.me.last_login_at) : '—' }}
            </span>
          </div>
        </div>
      </section>

      <!-- Второй фактор -->
      <section class="card flex flex-col gap-space-3">
        <div class="flex items-center justify-between">
          <h2 class="font-headline-sm text-headline-sm uppercase text-on-surface">
            Двухфакторная аутентификация
          </h2>
          <StatusBadge
            :label="auth.me?.totp_enabled ? 'Включена' : 'Выключена'"
            :tone="auth.me?.totp_enabled ? 'verified' : 'error'"
          />
        </div>

        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Осталось кодов восстановления:
          <span class="mono text-on-surface">{{ auth.me?.unused_recovery_codes ?? 0 }}</span>
        </p>

        <div class="mt-auto flex flex-wrap gap-space-2 pt-space-2">
          <RouterLink
            v-if="!auth.me?.totp_enabled"
            class="btn-primary"
            :to="{ name: 'totp-setup' }"
          >
            <span class="ms-icon text-[18px]">shield</span>
            Настроить
          </RouterLink>
          <button v-else class="btn-secondary" type="button" @click="openCodesForm">
            Перевыпустить коды восстановления
          </button>
        </div>
      </section>

      <!-- Сессии -->
      <section class="card flex flex-col gap-space-3">
        <h2 class="font-headline-sm text-headline-sm uppercase text-on-surface">Сессии</h2>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Если вы входили с чужого или потерянного устройства — завершите все сессии. Придётся
          войти заново, включая эту вкладку.
        </p>
        <button
          class="btn-secondary mt-auto self-start text-error"
          type="button"
          :disabled="busy"
          @click="logoutEverywhere"
        >
          <span class="ms-icon text-[18px]">logout</span>
          Завершить все сессии
        </button>
      </section>

      <!-- Пароль -->
      <section class="card flex flex-col gap-space-3">
        <h2 class="font-headline-sm text-headline-sm uppercase text-on-surface">Пароль</h2>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          После смены пароля все сессии завершаются — потребуется войти заново на каждом
          устройстве.
        </p>
        <button class="btn-secondary mt-auto self-start" type="button" @click="showPasswordForm = true">
          <span class="ms-icon text-[18px]">key</span>
          Сменить пароль
        </button>
      </section>
    </div>

    <!-- Смена пароля -->
    <ModalDialog
      v-if="showPasswordForm"
      title="Смена пароля"
      icon="key"
      :busy="busy"
      @close="showPasswordForm = false"
    >
      <div class="flex flex-col gap-space-3">
        <div>
          <label class="field-label" for="cur">Текущий пароль</label>
          <input id="cur" v-model="currentPassword" class="field" type="password" autocomplete="current-password" />
        </div>
        <div>
          <label class="field-label" for="new">Новый пароль (минимум 10 символов)</label>
          <input id="new" v-model="newPassword" class="field" type="password" autocomplete="new-password" />
        </div>
        <div>
          <label class="field-label" for="rep">Повторите новый пароль</label>
          <input id="rep" v-model="repeatPassword" class="field" type="password" autocomplete="new-password" />
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Сразу после смены вы будете разлогинены и вернётесь на экран входа.
        </p>
      </div>
      <template #actions>
        <button
          class="btn-primary"
          type="button"
          :disabled="busy || newPassword.length < 10"
          @click="changePassword"
        >
          {{ busy ? 'Меняем…' : 'Сменить пароль' }}
        </button>
      </template>
    </ModalDialog>

    <!-- Коды восстановления -->
    <ModalDialog
      v-if="showCodesForm"
      title="Коды восстановления"
      icon="password"
      :busy="busy"
      @close="showCodesForm = false"
    >
      <div class="flex flex-col gap-space-3">
        <template v-if="newCodes.length === 0">
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Прежние коды перестанут работать. Подтвердите действие кодом из приложения.
          </p>
          <div>
            <label class="field-label" for="totp">Код из приложения</label>
            <input
              id="totp"
              v-model="totpCode"
              class="field max-w-[200px] text-center font-headline-sm tracking-[0.3em]"
              type="text"
              inputmode="numeric"
              maxlength="6"
              placeholder="000000"
            />
          </div>
        </template>
        <template v-else>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Сохраните коды — они показываются один раз.
          </p>
          <div class="grid grid-cols-2 gap-space-2 rounded-lg bg-surface-container p-space-4">
            <code
              v-for="item in newCodes"
              :key="item"
              class="font-label-coordinate text-[14px] tracking-widest text-on-surface"
            >
              {{ item }}
            </code>
          </div>
        </template>
      </div>
      <template #actions>
        <button
          v-if="newCodes.length === 0"
          class="btn-primary"
          type="button"
          :disabled="busy || totpCode.trim().length < 6"
          @click="regenerate"
        >
          {{ busy ? 'Выпускаем…' : 'Перевыпустить' }}
        </button>
        <button v-else class="btn-primary" type="button" @click="showCodesForm = false">
          Я сохранил коды
        </button>
      </template>
    </ModalDialog>
  </div>
</template>
