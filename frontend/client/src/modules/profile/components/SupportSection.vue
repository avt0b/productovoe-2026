<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

const router = useRouter()
const session = useSessionStore()

/**
 * Выход в два нажатия: первое спрашивает, второе выходит. Случайный тап не
 * выкинет из приложения. Кнопка нейтральная: красный по контракту — только ошибки.
 */
const confirming = ref(false)

async function signOut(): Promise<void> {
  await session.signOut()
  await router.replace(router.hasRoute('auth') ? { name: 'auth' } : { name: 'home' })
}
</script>

<template>
  <section v-if="session.isAuthenticated" class="flex flex-col">
    <button
      type="button"
      class="flex w-full items-center justify-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-3 font-label-lg text-label-lg text-on-surface transition-colors duration-200 active:scale-[0.99]"
      :aria-expanded="confirming"
      @click="confirming = !confirming"
    >
      <MsIcon name="logout" :size="18" />
      Выйти из учётной записи
    </button>

    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="confirming ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="!confirming"
    >
      <div class="overflow-hidden">
        <div class="mt-space-sm flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document" role="alertdialog" aria-label="Подтверждение выхода">
          <p class="font-body-sm text-body-sm text-on-surface">
            Выйти из учётной записи? Отметки чек-листов и настройки останутся на телефоне.
          </p>
          <div class="flex gap-space-sm">
            <button
              type="button"
              class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
              @click="confirming = false"
            >
              Остаться
            </button>
            <button
              type="button"
              class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-inverse-surface py-2.5 font-label-md text-label-md text-inverse-on-surface active:scale-95 disabled:opacity-70"
              :disabled="session.pending"
              @click="signOut"
            >
              <MsIcon :name="session.pending ? 'progress_activity' : 'logout'" :size="18" :class="{ 'animate-spin': session.pending }" />
              Выйти
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
