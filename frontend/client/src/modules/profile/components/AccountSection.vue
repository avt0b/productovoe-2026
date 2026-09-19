<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { serverLabel } from '@/core/server'
import type { SessionUser } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

/** Учётная запись: почта и роль из `auth_service`, сервер, к которому подключено приложение. */
const props = defineProps<{ user: SessionUser }>()

const router = useRouter()

/** Выбор сервера — временный модуль. Уберут его — строка пропадёт. */
const canPickServer = computed(() => router.hasRoute('server'))
const server = computed(() => serverLabel())

const rows = computed(() => [
  { id: 'email', label: 'Почта для входа', value: props.user.email ?? 'Демо-режим без аккаунта', icon: 'mail' },
  { id: 'role', label: 'Роль на платформе', value: props.user.headline, icon: 'shield_person' },
])
</script>

<template>
  <section class="mt-2 flex flex-col gap-space-sm">
    <div class="px-1">
      <h3 class="font-headline-sm text-headline-sm text-on-surface">Учётная запись</h3>
      <span class="font-body-sm text-body-sm text-on-surface-variant">Роль меняет модератор платформы</span>
    </div>

    <div class="flex flex-col rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
      <template v-for="(row, index) in rows" :key="row.id">
        <div v-if="index > 0" class="my-space-md h-px bg-surface-container" />
        <div class="flex min-w-0 items-center gap-space-sm">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container text-on-surface-variant">
            <MsIcon :name="row.icon" :size="19" />
          </div>
          <div class="min-w-0">
            <span class="block font-label-sm text-label-sm text-outline">{{ row.label }}</span>
            <span class="block truncate font-label-lg text-label-lg font-semibold text-on-surface">{{ row.value }}</span>
          </div>
        </div>
      </template>

      <template v-if="canPickServer">
        <div class="my-space-md h-px bg-surface-container" />
        <RouterLink :to="{ name: 'server' }" class="flex min-w-0 items-center gap-space-sm">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container text-on-surface-variant">
            <MsIcon name="dns" :size="19" />
          </div>
          <div class="min-w-0 flex-1">
            <span class="block font-label-sm text-label-sm text-outline">Сервер (для тестов)</span>
            <span class="block truncate font-label-lg text-label-lg font-semibold text-on-surface">{{ server }}</span>
          </div>
          <MsIcon name="chevron_right" :size="20" class="text-outline" />
        </RouterLink>
      </template>
    </div>
  </section>
</template>
