<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'

import type { SessionUser } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'

/**
 * Жетон исследователя — номер профиля. По нему краевед находит человека и
 * подтверждает его, и тот же номер стоит в заявке на роль: администратор ищет
 * по нему заявителя. Раньше здесь был нарисованный QR из макета, который нельзя
 * отсканировать; генератора QR в зависимостях нет, поэтому показываем сам номер
 * и даём его передать.
 */
const props = defineProps<{ user: SessionUser }>()

const emit = defineEmits<{ close: [] }>()

const copied = ref(false)
let copiedTimer: ReturnType<typeof setTimeout> | undefined

/** Номер длинный — делим на группы, чтобы его можно было продиктовать. */
const groups = props.user.id.split('-')

async function pass(): Promise<void> {
  const text = `Жетон исследователя «Маршрутов победы»: ${props.user.name}, № ${props.user.id}`
  try {
    if (navigator.share) {
      await navigator.share({ title: 'Жетон исследователя', text })
      return
    }
    await navigator.clipboard.writeText(props.user.id)
    copied.value = true
    clearTimeout(copiedTimer)
    copiedTimer = setTimeout(() => (copied.value = false), 2000)
  } catch {
    /* человек закрыл окно «Поделиться» */
  }
}

onBeforeUnmount(() => clearTimeout(copiedTimer))
</script>

<template>
  <SheetDialog title="Жетон исследователя" :subtitle="user.name" @close="emit('close')">
    <div class="flex flex-col items-center gap-space-md text-center">
      <span class="flex h-14 w-14 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed">
        <MsIcon name="badge" :size="28" filled />
      </span>
      <p class="font-body-sm text-body-sm text-on-surface-variant">
        Передайте номер краеведу — он подтвердит ваш профиль. Этот же номер уходит в заявку на роль: по нему
        администратор платформы находит вас.
      </p>

      <div class="flex w-full flex-col items-center gap-space-xs rounded-2xl bg-surface-container-low p-space-md">
        <span class="font-archival text-archival uppercase text-on-surface-variant">Номер жетона</span>
        <p class="flex flex-wrap justify-center gap-x-space-xs font-label-lg text-label-lg tracking-wide text-on-surface" :aria-label="user.id">
          <span v-for="(group, index) in groups" :key="index">{{ group }}</span>
        </p>
      </div>

      <button
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="pass"
      >
        <MsIcon :name="copied ? 'check' : 'share'" :size="18" />
        <span>{{ copied ? 'Номер скопирован' : 'Передать номер' }}</span>
      </button>
    </div>
  </SheetDialog>
</template>
