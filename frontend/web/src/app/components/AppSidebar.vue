<script setup>
import { useRouter } from 'vue-router'
import { useAuthSession } from '@modules/auth'

defineProps({
  open: { type: Boolean, default: true },
})
const emit = defineEmits(['navigate', 'close'])

const router = useRouter()
const { session, logout } = useAuthSession()

async function switchAccount() {
  if (session.status === 'authenticated') {
    await logout()
  }
  emit('navigate')
  router.push('/auth')
}

const navItems = [
  { path: 'victory-routes', icon: 'route', label: 'Маршруты', href: '/routes' },
  { path: 'last-battle-registry', icon: 'location_searching', label: 'Последний бой', href: '/last-battle' },
  { path: 'expedition-hq', icon: 'campaign', label: 'Штаб', href: '/expedition-hq' },
  { path: 'squad-registration', icon: 'add_task', label: 'Отряды и заявки школ', href: '/squad-registration' },
  { path: 'fundraising', icon: 'volunteer_activism', label: 'Сборы', href: '/fundraising' },
  { path: 'living-memory-archive', icon: 'auto_stories', label: 'Живая память', href: '/living-memory' },
  { path: 'researcher-profile', icon: 'manage_accounts', label: 'Профиль исследователя', href: '/profile' },
]
</script>

<template>
  <aside
    class="fixed left-0 top-0 h-full w-72 max-w-[85vw] bg-surface-container-lowest z-50 flex flex-col justify-between py-6 px-5 shadow-[0_1px_8px_rgba(0,0,0,0.04)] transition-transform duration-300 ease-out"
    :class="open ? 'translate-x-0' : '-translate-x-full'"
  >
    <div class="flex flex-col gap-6">
      <div class="flex items-center justify-between gap-3 px-2">
        <div class="flex items-center gap-3 min-w-0">
          <div class="h-8 w-8 shrink-0 rounded-full bg-primary flex items-center justify-center">
            <span class="material-symbols-outlined text-on-primary text-[18px]" style="font-variation-settings: 'FILL' 1">
              military_tech
            </span>
          </div>
          <div class="flex flex-col min-w-0">
            <span class="font-headline-sm text-headline-sm text-on-surface tracking-tight leading-tight truncate">
              Маршруты победы
            </span>
            <span class="font-label-sm text-label-sm text-secondary uppercase tracking-wider truncate">
              Архивно-полевой центр
            </span>
          </div>
        </div>
        <button
          class="lg:hidden w-8 h-8 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high shrink-0"
          @click="$emit('close')"
        >
          <span class="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>

      <div class="px-2">
        <div class="bg-surface-container-low rounded-lg p-3 flex items-start gap-2.5">
          <span class="material-symbols-outlined text-primary text-[20px] shrink-0 mt-0.5">flag</span>
          <div class="flex flex-col">
            <span class="font-label-sm text-label-sm text-on-surface-variant uppercase">Оперативный статус</span>
            <span class="font-label-md text-label-md text-on-surface font-bold">Штаб активен: Орловский плацдарм</span>
          </div>
        </div>
      </div>

      <nav class="flex flex-col gap-1.5 pt-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.href"
          :data-tour="`nav-${item.href}`"
          class="flex items-center gap-3.5 px-3.5 py-3 rounded-DEFAULT font-label-lg text-label-lg transition-all"
          :class="
            item.href === $route.path
              ? 'bg-secondary-container text-on-secondary-container font-bold shadow-sm'
              : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
          "
          @click="$emit('navigate')"
        >
          <span class="material-symbols-outlined text-[22px]">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </div>

    <div class="flex flex-col gap-3 pt-4 border-t border-surface-container-high/60">
      <div class="bg-surface-container-low rounded-DEFAULT p-3 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <span class="material-symbols-outlined text-tertiary text-[20px]">military_tech</span>
          <div class="flex flex-col">
            <span class="font-label-sm text-label-sm text-on-surface-variant">Экспедиций</span>
            <span class="font-label-md text-label-md text-on-surface font-bold">14 пройдено</span>
          </div>
        </div>
        <span class="font-label-sm text-label-sm bg-tertiary-fixed text-on-tertiary-fixed px-2 py-0.5 rounded-full font-bold">
          Ранг III
        </span>
      </div>
      <button
        type="button"
        class="flex items-center justify-center gap-2 px-4 py-2.5 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md transition-colors"
        @click="switchAccount"
      >
        <span class="material-symbols-outlined text-[18px]">logout</span>
        <span>{{ session.status === 'authenticated' ? 'Выйти' : 'Сменить аккаунт' }}</span>
      </button>
    </div>
  </aside>
</template>
