<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { accountsApi } from '@/api/endpoints'
import type { AdminOut, AdminRole } from '@/api/types'
import ModalDialog from '@/components/ModalDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { errorText, formatDateTime } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const ROLES: Array<{ value: AdminRole; label: string; hint: string }> = [
  { value: 'superadmin', label: 'Суперадминистратор', hint: 'Всё, включая учётки администраторов' },
  { value: 'admin', label: 'Администратор', hint: 'Операции над пользователями и контентом' },
  { value: 'moderator', label: 'Модератор', hint: 'Модерация контента' },
  { value: 'viewer', label: 'Наблюдатель', hint: 'Только чтение: дашборд, списки, журнал' },
]
const roleLabel = (role: string): string => ROLES.find((r) => r.value === role)?.label ?? role

const query = ref('')
const list = useResourceList<AdminOut>((limit, offset) =>
  accountsApi.list({ query: query.value || undefined, limit, offset }),
)

const creating = ref(false)
const form = ref({ email: '', password: '', full_name: '', role: 'viewer' as AdminRole })
const busy = ref(false)
const actionError = ref<string | null>(null)
const pending = ref<string | null>(null)

function openCreate(): void {
  form.value = { email: '', password: '', full_name: '', role: 'viewer' }
  actionError.value = null
  creating.value = true
}

async function create(): Promise<void> {
  busy.value = true
  actionError.value = null
  try {
    await accountsApi.create({
      email: form.value.email.trim(),
      password: form.value.password,
      full_name: form.value.full_name.trim(),
      role: form.value.role,
    })
    creating.value = false
    await list.reload()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    busy.value = false
  }
}

async function toggleActive(admin: AdminOut): Promise<void> {
  pending.value = admin.id
  actionError.value = null
  try {
    await accountsApi.setActive(admin.id, !admin.is_active)
    await list.load()
  } catch (e) {
    // Последнего суперадминистратора отключить нельзя — бэкенд объяснит почему.
    actionError.value = errorText(e)
  } finally {
    pending.value = null
  }
}

async function resetTotp(admin: AdminOut): Promise<void> {
  pending.value = admin.id
  actionError.value = null
  try {
    await accountsApi.resetTotp(admin.id)
    await list.load()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    pending.value = null
  }
}

onMounted(list.load)
</script>

<template>
  <div class="flex flex-col gap-space-6">
    <PageHeader
      eyebrow="Контур админки"
      title="Учётные записи администраторов"
      subtitle="Отдельны от пользователей платформы. Вход требует второго фактора."
    >
      <template #actions>
        <button class="btn-primary" type="button" @click="openCreate">
          <span class="ms-icon text-[18px]">person_add</span>
          Добавить администратора
        </button>
      </template>
    </PageHeader>

    <div class="card flex flex-col items-stretch gap-space-3 lg:flex-row lg:items-center">
      <div class="relative flex-1">
        <span class="ms-icon absolute left-space-3 top-1/2 -translate-y-1/2 text-[20px] text-outline">
          search
        </span>
        <input
          v-model="query"
          class="field pl-10"
          type="search"
          placeholder="Поиск по email или имени"
          @keyup.enter="list.reload"
        />
      </div>
      <button class="btn-primary" type="button" @click="list.reload">Найти</button>
    </div>

    <p
      v-if="actionError && !creating"
      class="rounded-lg bg-error-container px-space-4 py-space-3 font-body-sm text-body-sm text-on-error-container"
      role="alert"
    >
      {{ actionError }}
    </p>

    <StateBlock
      :loading="list.loading.value"
      :error="list.error.value"
      :empty="list.items.value.length === 0"
      empty-text="Администраторов нет"
      empty-icon="admin_panel_settings"
      @retry="list.load"
    >
      <div class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead class="table-head">
              <tr>
                <th>Администратор</th>
                <th>Роль</th>
                <th>Второй фактор</th>
                <th>Последний вход</th>
                <th>Статус</th>
                <th class="text-right">Действия</th>
              </tr>
            </thead>
            <tbody class="font-body-md text-body-md">
              <tr
                v-for="admin in list.items.value"
                :key="admin.id"
                class="table-row"
                :class="!admin.is_active && 'bg-error-container/20'"
              >
                <td>
                  <div class="flex flex-col">
                    <span class="font-medium text-on-surface">
                      {{ admin.full_name || admin.email }}
                      <span v-if="admin.id === auth.me?.id" class="mono text-secondary">· это вы</span>
                    </span>
                    <span class="mono text-outline">{{ admin.email }}</span>
                  </div>
                </td>
                <td>
                  <span class="font-label-action text-label-action uppercase text-primary">
                    {{ roleLabel(admin.role) }}
                  </span>
                </td>
                <td>
                  <StatusBadge
                    :label="admin.totp_enabled ? 'Настроен' : 'Не настроен'"
                    :tone="admin.totp_enabled ? 'verified' : 'pending'"
                  />
                </td>
                <td class="mono whitespace-nowrap text-on-surface-variant">
                  {{ admin.last_login_at ? formatDateTime(admin.last_login_at) : 'ни разу' }}
                </td>
                <td>
                  <StatusBadge
                    :label="admin.is_active ? 'Активен' : 'Отключён'"
                    :tone="admin.is_active ? 'verified' : 'error'"
                  />
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end gap-space-2">
                    <button
                      v-if="admin.totp_enabled"
                      class="btn-secondary btn-sm"
                      type="button"
                      :disabled="pending === admin.id"
                      title="Снять 2FA, если утеряны телефон и коды восстановления"
                      @click="resetTotp(admin)"
                    >
                      Сбросить 2FA
                    </button>
                    <button
                      class="btn-sm"
                      :class="admin.is_active ? 'btn-ghost text-error' : 'btn-secondary'"
                      type="button"
                      :disabled="pending === admin.id || admin.id === auth.me?.id"
                      @click="toggleActive(admin)"
                    >
                      {{ admin.is_active ? 'Отключить' : 'Включить' }}
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <PaginationBar
          :total="list.total.value"
          :limit="list.limit.value"
          :offset="list.offset.value"
          @update:offset="list.setOffset"
        />
      </div>
    </StateBlock>

    <ModalDialog
      v-if="creating"
      title="Новый администратор"
      icon="person_add"
      :busy="busy"
      @close="creating = false"
    >
      <div class="flex flex-col gap-space-3">
        <div>
          <label class="field-label" for="new-email">Служебная почта</label>
          <input
            id="new-email"
            v-model="form.email"
            class="field"
            type="email"
            placeholder="ivanov@marshruty.ru"
          />
        </div>
        <div>
          <label class="field-label" for="new-name">ФИО</label>
          <input id="new-name" v-model="form.full_name" class="field" type="text" />
        </div>
        <div>
          <label class="field-label" for="new-password">Временный пароль (минимум 10 символов)</label>
          <input
            id="new-password"
            v-model="form.password"
            class="field"
            type="text"
            autocomplete="new-password"
          />
        </div>
        <div>
          <span class="field-label">Роль</span>
          <div class="flex flex-col gap-space-2">
            <label
              v-for="role in ROLES"
              :key="role.value"
              class="flex cursor-pointer items-start gap-space-3 rounded-lg bg-surface-container p-space-3 hover:bg-surface-container-high"
            >
              <input v-model="form.role" class="mt-1" type="radio" :value="role.value" name="admin-role" />
              <div class="flex flex-col">
                <span class="font-label-action text-label-action uppercase text-on-surface">
                  {{ role.label }}
                </span>
                <span class="font-body-sm text-body-sm text-on-surface-variant">{{ role.hint }}</span>
              </div>
            </label>
          </div>
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          При первом входе администратор обязан настроить второй фактор — до этого остальные
          разделы панели ему закрыты.
        </p>
        <p v-if="actionError" class="font-body-sm text-body-sm text-error">{{ actionError }}</p>
      </div>
      <template #actions>
        <button
          class="btn-primary"
          type="button"
          :disabled="busy || !form.email || form.password.length < 10"
          @click="create"
        >
          {{ busy ? 'Создаём…' : 'Создать' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>
