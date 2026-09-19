<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText, formatMoney } from '@/core/format'
import { useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { donate, type Need, type Squad } from '../data'

const props = defineProps<{ need: Need; squad: Squad | undefined }>()

/** `donated` — собранная сумма и статус сбора изменились, экрану пора их перечитать. */
const emit = defineEmits<{ close: []; donated: [] }>()

const PRESETS = [100, 500, 1000, 3000] as const
/** Лимит сервиса на один взнос. */
const MAX_AMOUNT = 10_000_000

const session = useSessionStore()
const amount = ref<number | null>(500)
const comment = ref('')
const sending = ref(false)
const error = ref<string | null>(null)
const done = ref<number | null>(null)

const valid = computed(() => amount.value !== null && Number.isInteger(amount.value) && amount.value >= 1 && amount.value <= MAX_AMOUNT)

async function submit(): Promise<void> {
  if (!valid.value || sending.value || amount.value === null) return
  sending.value = true
  error.value = null
  try {
    const sent = amount.value
    await donate(props.need.id, sent, comment.value.trim())
    done.value = sent
    emit('donated')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <SheetDialog :title="need.title" :subtitle="squad?.name" @close="emit('close')">
    <AccountRequired v-if="!session.hasAccount" text="Помочь отряду можно с аккаунтом" />

    <div v-else-if="done !== null" class="flex flex-col items-center gap-space-md py-space-md text-center">
      <div class="flex h-14 w-14 items-center justify-center rounded-full bg-secondary-container text-secondary">
        <MsIcon name="volunteer_activism" :size="30" filled />
      </div>
      <p class="font-headline-sm text-headline-sm text-on-surface">Спасибо! {{ formatMoney(done) }} добавлено к сбору</p>
      <button
        type="button"
        class="w-full rounded-full bg-secondary py-3 font-label-lg text-label-lg text-on-secondary"
        @click="emit('close')"
      >
        Готово
      </button>
    </div>

    <form v-else class="flex flex-col gap-space-md" @submit.prevent="submit">
      <!-- Оплаты нет: без этой строки человек решит, что деньги ушли отряду. -->
      <InlineNotice icon="science">
        Тестовый взнос: оплата через ЮKassa ещё не подключена, деньги не списываются — сумма только добавится к сбору.
      </InlineNotice>

      <div class="grid grid-cols-4 gap-space-xs">
        <button
          v-for="preset in PRESETS"
          :key="preset"
          type="button"
          class="rounded-full py-2 font-label-md text-label-md transition-colors"
          :class="amount === preset ? 'bg-primary text-on-primary' : 'bg-surface-container-low text-on-surface'"
          @click="amount = preset"
        >
          {{ formatMoney(preset) }}
        </button>
      </div>

      <FormInput v-model="amount" label="Сумма, ₽" type="number" inputmode="numeric" :min="1" :max="MAX_AMOUNT" :step="1" required />
      <FormTextarea v-model="comment" label="Пожелание отряду" :rows="2" :maxlength="500" placeholder="Необязательно" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!valid || sending"
      >
        <MsIcon :name="sending ? 'progress_activity' : 'volunteer_activism'" :size="20" :class="{ 'animate-spin': sending }" />
        {{ valid && amount ? `Помочь на ${formatMoney(amount)}` : 'Укажите сумму' }}
      </button>
    </form>
  </SheetDialog>
</template>
