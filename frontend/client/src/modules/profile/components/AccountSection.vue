<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { serverLabel } from '@/core/server'
import type { SessionUser } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

import { ROLES } from '../data'

/** Учётная запись: почта и роль из `auth_service`, сервер, к которому подключено приложение. */
const props = defineProps<{ user: SessionUser }>()

const router = useRouter()

/** Выбор сервера — временный модуль. Уберут его — строка пропадёт. */
const canPickServer = computed(() => router.hasRoute('server'))
const server = computed(() => serverLabel())

const rows = computed(() => [
  { id: 'email', label: 'Почта для входа', value: props.user.email ?? 'Демо-режим без аккаунта', icon: 'mail' },
  {
    id: 'role',
    label: 'Роль на платформе',
    value: props.user.role ? ROLES[props.user.role].title : props.user.headline || 'Без роли',
    icon: 'shield_person',
  },
])
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div>
      <p class="font-archival text-archival uppercase text-on-surface-variant">Вход и подключение</p>
      <h2 class="font-headline-md text-headline-md text-on-surface">Учётная запись</h2>
    </div>

    <div class="flex flex-col divide-y divide-outline-variant/60 rounded-2xl bg-surface-container-lowest px-space-md shadow-document">
      <div v-for="row in rows" :key="row.id" class="flex min-w-0 items-center gap-space-sm py-space-sm">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface-variant" aria-hidden="true">
          <MsIcon :name="row.icon" :size="18" />
        </span>
        <div class="min-w-0">
          <span class="block font-label-sm text-label-sm text-on-surface-variant">{{ row.label }}</span>
          <span class="block truncate font-label-lg text-label-lg text-on-surface">{{ row.value }}</span>
        </div>
      </div>

      <RouterLink v-if="canPickServer" :to="{ name: 'server' }" class="flex min-w-0 items-center gap-space-sm py-space-sm">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface-variant" aria-hidden="true">
          <MsIcon name="dns" :size="18" />
        </span>
        <div class="min-w-0 flex-1">
          <span class="block font-label-sm text-label-sm text-on-surface-variant">Сервер (для тестов)</span>
          <span class="block truncate font-label-lg text-label-lg text-on-surface">{{ server }}</span>
        </div>
        <MsIcon name="chevron_right" :size="20" class="text-on-surface-variant" />
      </RouterLink>
    </div>
  </section>
</template>
