<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/core/session'

import MsIcon from './MsIcon.vue'

const router = useRouter()
const session = useSessionStore()

/** Аватар ведёт в профиль, только если модуль профиля подключён. */
const profileAvailable = computed(() => router.hasRoute('profile'))

const initials = computed(() =>
  (session.user?.name ?? '')
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase(),
)
</script>

<template>
  <component
    :is="profileAvailable ? 'RouterLink' : 'div'"
    :to="profileAvailable ? { name: 'profile' } : undefined"
    class="ml-space-xs flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary-fixed text-primary"
    :aria-label="profileAvailable ? 'Профиль' : undefined"
  >
    <img
      v-if="session.user?.avatarUrl"
      :src="session.user.avatarUrl"
      alt=""
      class="h-full w-full object-cover"
    />
    <span v-else-if="initials" class="font-label-sm text-label-sm">{{ initials }}</span>
    <MsIcon v-else name="person" :size="18" />
  </component>
</template>
