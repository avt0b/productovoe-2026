<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const nav = useRouter()
const menuOpen = ref(false)

const ROLE_LABELS: Record<string, string> = {
  superadmin: 'Суперадминистратор',
  admin: 'Администратор',
  moderator: 'Модератор',
  viewer: 'Наблюдатель',
}

/** Меню строится из роутов — один источник правды, не разъедется с навигацией. */
const links = computed(() =>
  nav
    .getRoutes()
    .filter((route) => route.meta.nav && (!route.meta.superadmin || auth.isSuperadmin))
    .map((route) => ({
      name: String(route.name),
      title: route.meta.nav!.title,
      icon: route.meta.nav!.icon,
      group: route.meta.nav!.group,
    })),
)

const mainLinks = computed(() => links.value.filter((l) => l.group === 'main'))
const systemLinks = computed(() => links.value.filter((l) => l.group === 'system'))

async function signOut(): Promise<void> {
  await auth.logout()
  await nav.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <header
      class="fixed inset-x-0 top-0 z-50 h-16 bg-surface/90 shadow-[0_1px_8px_rgba(0,0,0,0.04)] backdrop-blur-md"
    >
      <div class="flex h-16 items-center justify-between gap-space-4 px-margin-desktop">
        <div class="flex items-center gap-space-4">
          <button
            class="rounded-lg p-space-2 text-on-surface-variant hover:bg-surface-container lg:hidden"
            type="button"
            aria-label="Открыть меню"
            @click="menuOpen = !menuOpen"
          >
            <span class="ms-icon text-[22px]">menu</span>
          </button>

          <svg class="h-8 w-8 shrink-0" viewBox="0 0 32 32" aria-hidden="true">
            <circle cx="16" cy="16" r="15" fill="none" stroke="#495d38" stroke-width="1.5" />
            <path
              d="M16 6l2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-3-5.3 3 1.1-6-4.4-4.2 6-.8z"
              fill="#495d38"
            />
            <path
              d="M5 24c4-3 8 1 11-1s6-4 11-2"
              fill="none"
              stroke="#51643a"
              stroke-width="1.5"
              stroke-dasharray="2 2"
              stroke-linecap="round"
            />
          </svg>

          <div class="flex flex-col">
            <span class="font-headline-sm text-headline-sm uppercase tracking-wide text-primary">
              Маршруты победы
            </span>
            <span
              class="font-label-archive-code text-label-archive-code uppercase tracking-wider text-on-surface-variant"
            >
              Панель администратора
            </span>
          </div>
        </div>

        <div class="flex items-center gap-space-3">
          <div class="hidden flex-col text-right md:flex">
            <span class="font-label-action text-label-action text-on-surface">
              {{ auth.me?.full_name || auth.me?.email }}
            </span>
            <span class="font-label-archive-code text-label-archive-code text-secondary">
              {{ ROLE_LABELS[auth.me?.role ?? ''] ?? auth.me?.role }}
            </span>
          </div>
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary">
            <span class="ms-icon text-[18px] text-on-primary">person</span>
          </div>
          <button class="btn-ghost btn-sm" type="button" @click="signOut">
            <span class="ms-icon text-[18px]">logout</span>
            <span class="hidden sm:inline">Выйти</span>
          </button>
        </div>
      </div>
    </header>

    <aside
      class="fixed bottom-0 left-0 top-16 z-40 w-72 overflow-y-auto bg-surface-container-low px-space-4 py-space-6 transition-transform lg:translate-x-0"
      :class="menuOpen ? 'translate-x-0' : '-translate-x-full'"
      @click="menuOpen = false"
    >
      <nav class="flex flex-col gap-space-6">
        <div class="flex flex-col gap-space-1">
          <span
            class="px-space-3 pb-space-1 font-label-archive-code text-label-archive-code uppercase tracking-widest text-outline"
          >
            Оперативная разметка
          </span>
          <RouterLink
            v-for="link in mainLinks"
            :key="link.name"
            :to="{ name: link.name }"
            class="flex items-center gap-space-3 rounded-lg px-space-3 py-space-2 text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
            active-class="!bg-primary-container !text-on-primary font-bold"
          >
            <span class="ms-icon text-[20px]">{{ link.icon }}</span>
            <span class="font-label-action text-label-action uppercase">{{ link.title }}</span>
          </RouterLink>
        </div>

        <div class="flex flex-col gap-space-1">
          <span
            class="px-space-3 pb-space-1 font-label-archive-code text-label-archive-code uppercase tracking-widest text-outline"
          >
            Система
          </span>
          <RouterLink
            v-for="link in systemLinks"
            :key="link.name"
            :to="{ name: link.name }"
            class="flex items-center gap-space-3 rounded-lg px-space-3 py-space-2 text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
            active-class="!bg-primary-container !text-on-primary font-bold"
          >
            <span class="ms-icon text-[20px]">{{ link.icon }}</span>
            <span class="font-label-action text-label-action uppercase">{{ link.title }}</span>
          </RouterLink>
        </div>
      </nav>

      <div
        v-if="!auth.canWrite"
        class="mt-space-6 rounded-lg bg-surface-container p-space-3 font-body-sm text-body-sm text-on-surface-variant"
      >
        <span class="ms-icon align-middle text-[16px] text-tertiary">visibility</span>
        Режим наблюдателя: изменения недоступны.
      </div>
    </aside>

    <div
      v-if="menuOpen"
      class="fixed inset-0 z-30 bg-black/40 lg:hidden"
      @click="menuOpen = false"
    />

    <main class="px-margin-desktop pb-space-12 pt-16 lg:pl-[calc(18rem+32px)]">
      <div class="mx-auto w-full max-w-[1560px] py-space-6">
        <slot />
      </div>
    </main>
  </div>
</template>
