<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

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
  <section v-if="session.isAuthenticated" class="flex flex-col">
    <button
      v-if="!confirming"
      type="button"
      class="flex w-full items-center justify-center gap-space-xs rounded-full bg-error-container px-4 py-3.5 font-label-lg text-label-lg text-on-error-container shadow-sm transition-opacity hover:opacity-90 active:scale-[0.99]"
      @click="confirming = true"
    >
      <MsIcon name="logout" :size="20" />
      <span>Выйти из учётной записи</span>
    </button>

    <div
      v-else
      class="flex flex-col gap-space-sm rounded-DEFAULT bg-error-container p-space-md"
      role="alertdialog"
      aria-label="Подтверждение выхода"
    >
      <p class="font-body-sm text-body-sm text-on-error-container">
        Выйти из учётной записи? Несохранённые оффлайн-метки останутся в памяти телефона.
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
          <MsIcon
            :name="session.pending ? 'progress_activity' : 'logout'"
            :size="18"
            :class="{ 'animate-spin': session.pending }"
          />
          Выйти
        </button>
      </div>
    </div>
  </section>
</template>
