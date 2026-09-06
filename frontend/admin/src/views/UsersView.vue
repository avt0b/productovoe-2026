<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { opsApi } from '@/api/endpoints'
import type { PlatformRole, PlatformUser } from '@/api/types'
import ModalDialog from '@/components/ModalDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { errorText, formatDate } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const ROLES: Array<{ value: PlatformRole; label: string; hint: string }> = [
  { value: 'family', label: 'Семья', hint: 'Маршруты и квесты, без прав редактирования' },
  { value: 'searcher', label: 'Поисковик', hint: 'Точки «Последнего боя», выезды, отряд' },
  { value: 'local_historian', label: 'Краевед', hint: 'Проверка и дополнение записей архива' },
  { value: 'mentor', label: 'Наставник', hint: 'Экскурсии для школ и клубов, маршруты' },
  { value: 'moderator', label: 'Модератор', hint: 'Модерация архива и статусов точек' },
]

const roleLabel = (role: string): string => ROLES.find((r) => r.value === role)?.label ?? role

const query = ref('')
const roleFilter = ref('')
const activeFilter = ref('')

const list = useResourceList<PlatformUser>((limit, offset) =>
  opsApi.users({
    query: query.value || undefined,
    role: roleFilter.value || undefined,
    is_active: activeFilter.value === '' ? undefined : activeFilter.value === 'true',
    limit,
    offset,
  }),
)

// --- диалоги ---
const roleTarget = ref<PlatformUser | null>(null)
const nextRole = ref<PlatformRole>('family')
const blockTarget = ref<PlatformUser | null>(null)
const blockReason = ref('')
const busy = ref(false)
const actionError = ref<string | null>(null)

function openRole(user: PlatformUser): void {
  roleTarget.value = user
  nextRole.value = user.role
  actionError.value = null
}

function openBlock(user: PlatformUser): void {
  blockTarget.value = user
  blockReason.value = ''
  actionError.value = null
}

async function saveRole(): Promise<void> {
  if (!roleTarget.value) return
  busy.value = true
  actionError.value = null
  try {
    await opsApi.setUserRole(roleTarget.value.id, nextRole.value)
    roleTarget.value = null
    await list.load()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    busy.value = false
  }
}

async function toggleBlock(): Promise<void> {
  const user = blockTarget.value
  if (!user) return
  busy.value = true
  actionError.value = null
  try {
    await opsApi.setUserActive(user.id, !user.is_active, blockReason.value.trim())
    blockTarget.value = null
    await list.load()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    busy.value = false
  }
}

onMounted(list.load)
</script>

<template>
  <div class="flex flex-col gap-space-6">
    <PageHeader
      eyebrow="Реестр платформы"
      title="Пользователи и роли"
      subtitle="Роль определяет, что человек может делать в приложении. Право верификации даёт подтверждённый статус в профиле."
    />

    <!-- Фильтры -->
    <div class="card flex flex-col items-stretch gap-space-3 lg:flex-row lg:items-center">
      <div class="relative flex-1">
        <span class="ms-icon absolute left-space-3 top-1/2 -translate-y-1/2 text-[20px] text-outline">
          search
        </span>
        <input
          v-model="query"
          class="field pl-10"
          type="search"
          placeholder="Поиск по email"
          @keyup.enter="list.reload"
        />
      </div>
      <select v-model="roleFilter" class="field lg:w-56" @change="list.reload">
        <option value="">Все роли</option>
        <option v-for="role in ROLES" :key="role.value" :value="role.value">{{ role.label }}</option>
      </select>
      <select v-model="activeFilter" class="field lg:w-48" @change="list.reload">
        <option value="">Любой статус</option>
        <option value="true">Активные</option>
        <option value="false">Заблокированные</option>
      </select>
      <button class="btn-primary" type="button" @click="list.reload">Найти</button>
    </div>

    <StateBlock
      :loading="list.loading.value"
      :error="list.error.value"
      :empty="list.items.value.length === 0"
      empty-text="Пользователи по заданным условиям не найдены"
      empty-icon="group_off"
      @retry="list.load"
    >
      <div class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead class="table-head">
              <tr>
                <th>Пользователь</th>
                <th>Роль</th>
                <th>Доступ</th>
                <th>Регистрация</th>
                <th class="text-right">Действия</th>
              </tr>
            </thead>
            <tbody class="font-body-md text-body-md">
              <tr
                v-for="user in list.items.value"
                :key="user.id"
                class="table-row"
                :class="!user.is_active && 'bg-error-container/20'"
              >
                <td>
                  <div class="flex flex-col">
                    <span class="font-medium text-on-surface">{{ user.email }}</span>
                    <span class="mono text-outline">{{ user.id.slice(0, 8) }}</span>
                  </div>
                </td>
                <td>
                  <span class="font-label-action text-label-action uppercase text-primary">
                    {{ roleLabel(user.role) }}
                  </span>
                </td>
                <td>
                  <div class="flex flex-wrap items-center gap-space-2">
                    <StatusBadge
                      :label="user.is_active ? 'Активен' : 'Заблокирован'"
                      :tone="user.is_active ? 'verified' : 'error'"
                    />
                    <StatusBadge v-if="user.is_root" label="is_root" tone="info" />
                  </div>
                </td>
                <td class="mono whitespace-nowrap text-on-surface-variant">
                  {{ formatDate(user.created_at) }}
                </td>
                <td class="text-right">
                  <div class="flex items-center justify-end gap-space-2">
                    <button
                      class="btn-secondary btn-sm"
                      type="button"
                      :disabled="!auth.canWrite"
                      @click="openRole(user)"
                    >
                      Роль
                    </button>
                    <button
                      class="btn-sm"
                      :class="user.is_active ? 'btn-ghost text-error' : 'btn-secondary'"
                      type="button"
                      :disabled="!auth.canWrite"
                      :title="user.is_active ? 'Заблокировать' : 'Разблокировать'"
                      @click="openBlock(user)"
                    >
                      <span class="ms-icon text-[18px]">
                        {{ user.is_active ? 'gavel' : 'lock_open' }}
                      </span>
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

    <!-- Смена роли -->
    <ModalDialog
      v-if="roleTarget"
      title="Изменение роли"
      icon="manage_accounts"
      :busy="busy"
      @close="roleTarget = null"
    >
      <div class="flex flex-col gap-space-3">
        <div>
          <span class="field-label">Пользователь</span>
          <span class="font-body-memorial-name text-body-memorial-name text-on-surface">
            {{ roleTarget.email }}
          </span>
        </div>
        <label
          v-for="role in ROLES"
          :key="role.value"
          class="flex cursor-pointer items-start gap-space-3 rounded-lg bg-surface-container p-space-3 hover:bg-surface-container-high"
        >
          <input v-model="nextRole" class="mt-1" type="radio" :value="role.value" name="role" />
          <div class="flex flex-col">
            <span class="font-label-action text-label-action uppercase text-on-surface">
              {{ role.label }}
            </span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">{{ role.hint }}</span>
          </div>
        </label>
        <p v-if="actionError" class="font-body-sm text-body-sm text-error">{{ actionError }}</p>
      </div>
      <template #actions>
        <button class="btn-primary" type="button" :disabled="busy" @click="saveRole">
          {{ busy ? 'Сохраняем…' : 'Обновить роль' }}
        </button>
      </template>
    </ModalDialog>

    <!-- Блокировка -->
    <ModalDialog
      v-if="blockTarget"
      :title="blockTarget.is_active ? 'Блокировка пользователя' : 'Восстановление доступа'"
      :icon="blockTarget.is_active ? 'gavel' : 'lock_open'"
      :tone="blockTarget.is_active ? 'danger' : 'primary'"
      :busy="busy"
      @close="blockTarget = null"
    >
      <div class="flex flex-col gap-space-3">
        <div class="rounded-lg bg-surface-container p-space-3">
          <span class="field-label">Пользователь</span>
          <span class="font-body-memorial-name text-body-memorial-name text-on-surface">
            {{ blockTarget.email }}
          </span>
        </div>
        <div>
          <label class="field-label" for="reason">Основание (попадёт в журнал аудита)</label>
          <textarea
            id="reason"
            v-model="blockReason"
            class="field h-auto py-space-2"
            rows="3"
            placeholder="Например: публикация точных координат неподнятых останков"
          />
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Блокировка отзывает все активные сессии пользователя. Срок пока не задаётся — в бэкенде
          хранится только флаг доступа.
        </p>
        <p v-if="actionError" class="font-body-sm text-body-sm text-error">{{ actionError }}</p>
      </div>
      <template #actions>
        <button
          :class="blockTarget.is_active ? 'btn-danger' : 'btn-primary'"
          type="button"
          :disabled="busy"
          @click="toggleBlock"
        >
          {{ blockTarget.is_active ? 'Заблокировать' : 'Восстановить доступ' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>
