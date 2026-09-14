<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

defineProps<{ curator: string }>()

const router = useRouter()
const session = useSessionStore()

/** Выход в два нажатия: первое спрашивает, второе выходит. Случайный тап не выкинет из приложения. */
const confirming = ref(false)

async function signOut(): Promise<void> {
  await session.signOut()
  await router.replace(router.hasRoute('auth') ? { name: 'auth' } : { name: 'home' })
}
</script>

<template>
  <section class="mt-2 flex flex-col gap-space-xs">
    <a
      href="#"
      class="flex items-center justify-between rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm transition-colors hover:bg-surface-container-low"
    >
      <div class="flex items-center gap-space-sm">
        <div class="flex h-9 w-9 items-center justify-center rounded-full bg-primary-fixed text-primary">
          <MsIcon name="support_agent" :size="20" />
        </div>
        <div>
          <h4 class="font-label-lg text-label-lg font-bold text-on-surface">Штаб отряда и куратор</h4>
          <p class="font-body-sm text-body-sm text-on-surface-variant">{{ curator }}</p>
        </div>
      </div>
      <MsIcon name="chevron_right" :size="20" class="text-outline" />
    </a>

    <a
      href="#"
      class="flex items-center justify-between rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm transition-colors hover:bg-surface-container-low"
    >
      <div class="flex items-center gap-space-sm">
        <div class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container text-on-surface-variant">
          <MsIcon name="policy" :size="20" />
        </div>
        <div>
          <h4 class="font-label-lg text-label-lg font-bold text-on-surface">Политика конфиденциальности</h4>
          <p class="font-body-sm text-body-sm text-on-surface-variant">Безопасность архивных и геолокационных данных</p>
        </div>
      </div>
      <MsIcon name="chevron_right" :size="20" class="text-outline" />
    </a>

    <button
      type="button"
      class="mt-2 flex w-full items-center justify-center gap-space-xs rounded-DEFAULT bg-surface-container-high px-4 py-3 font-label-lg text-label-lg text-on-surface shadow-sm transition-colors hover:bg-surface-container-highest active:scale-[0.99]"
    >
      <MsIcon name="sync" :size="19" class="text-secondary" />
      <span>Синхронизировать полевые заметки</span>
    </button>

    <template v-if="session.isAuthenticated">
      <button
        v-if="!confirming"
        type="button"
        class="mt-2 flex w-full items-center justify-center gap-space-xs rounded-full bg-error-container px-4 py-3.5 font-label-lg text-label-lg text-on-error-container shadow-sm transition-opacity hover:opacity-90 active:scale-[0.99]"
        @click="confirming = true"
      >
        <MsIcon name="logout" :size="20" />
        <span>Выйти из учетной записи исследователя</span>
      </button>

      <div v-else class="mt-2 flex flex-col gap-space-sm rounded-DEFAULT bg-error-container p-space-md" role="alertdialog" aria-label="Подтверждение выхода">
        <p class="font-body-sm text-body-sm text-on-error-container">
          Выйти из учетной записи? Несохраненные оффлайн-метки останутся в памяти телефона.
        </p>
        <div class="flex gap-space-sm">
          <button
            type="button"
            class="flex-1 rounded-full bg-surface-container-lowest py-2.5 font-label-md text-label-md text-on-surface"
            @click="confirming = false"
          >
            Остаться
          </button>
          <button
            type="button"
            class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error disabled:opacity-70"
            :disabled="session.pending"
            @click="signOut"
          >
            <MsIcon :name="session.pending ? 'progress_activity' : 'logout'" :size="18" :class="{ 'animate-spin': session.pending }" />
            Выйти
          </button>
        </div>
      </div>
    </template>
  </section>
</template>
