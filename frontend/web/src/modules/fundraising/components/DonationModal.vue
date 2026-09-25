<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as fundraisingApi from '../api.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  campaign: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'donated'])

const { session } = useAuthSession()

const amounts = [100, 300, 500, 1000]
const methods = [
  { id: 'card', label: 'Банковская карта', icon: 'credit_card' },
  { id: 'sbp', label: 'СБП', icon: 'qr_code_2' },
  { id: 'yoomoney', label: 'ЮMoney', icon: 'account_balance_wallet' },
]

const form = reactive({ amount: 300, customAmount: '', method: 'card' })
const step = ref('form')
const error = ref('')

const effectiveAmount = computed(() => Number(form.customAmount) || form.amount)

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      step.value = 'form'
      error.value = ''
    }
  },
)

function pickAmount(value) {
  form.amount = value
  form.customAmount = ''
}

async function pay() {
  if (!effectiveAmount.value || effectiveAmount.value < 10) return
  if (session.status !== 'authenticated') {
    error.value = 'Войдите, чтобы оформить пожертвование'
    return
  }
  step.value = 'processing'
  try {
    // Бэкенд пока не интегрирован с платёжным провайдером (интеграция
    // ЮKassa/CloudPayments в планах). Реально сохраняется сумма и
    // комментарий, деньги физически не списываются.
    const methodLabel = methods.find((m) => m.id === form.method)?.label
    await fundraisingApi.donate(session.accessToken, props.campaign.id, {
      amount: effectiveAmount.value,
      comment: `Демо-оплата: ${methodLabel}`,
    })
    emit('donated', { needId: props.campaign.id, amount: effectiveAmount.value })
    step.value = 'done'
  } catch (err) {
    step.value = 'form'
    error.value = err.detail ?? 'Не удалось оформить пожертвование'
  }
}

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-md w-full p-6 shadow-2xl flex flex-col gap-5">
      <div class="flex items-center justify-between">
        <div class="flex flex-col">
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold">Поддержать отряд</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ campaign?.squadName }}</span>
        </div>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <template v-if="step === 'form'">
        <div class="grid grid-cols-4 gap-2">
          <button
            v-for="amount in amounts"
            :key="amount"
            class="py-2.5 rounded-full font-label-md text-label-md font-bold transition-all"
            :class="
              form.amount === amount && !form.customAmount
                ? 'bg-primary text-on-primary'
                : 'bg-surface-container-low text-on-surface hover:bg-surface-container'
            "
            @click="pickAmount(amount)"
          >
            {{ amount }} ₽
          </button>
        </div>

        <input
          v-model="form.customAmount"
          type="number"
          min="10"
          placeholder="Своя сумма, ₽"
          class="w-full h-12 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />

        <div class="flex flex-col gap-2">
          <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Способ оплаты</span>
          <label
            v-for="method in methods"
            :key="method.id"
            class="flex items-center gap-3 p-3 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container cursor-pointer transition-colors"
          >
            <input v-model="form.method" type="radio" :value="method.id" class="w-4 h-4 accent-primary cursor-pointer" />
            <span class="material-symbols-outlined text-[20px] text-on-surface-variant">{{ method.icon }}</span>
            <span class="font-body-md text-body-md text-on-surface">{{ method.label }}</span>
          </label>
        </div>

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold text-center">{{ error }}</p>

        <button
          class="h-12 rounded-full bg-primary text-on-primary font-label-lg text-label-lg font-bold shadow-md hover:opacity-95 transition-all flex items-center justify-center gap-2"
          @click="pay"
        >
          <span class="material-symbols-outlined text-[18px]">volunteer_activism</span>
          <span>Пожертвовать {{ effectiveAmount }} ₽</span>
        </button>
        <span class="text-center font-body-sm text-body-sm text-on-surface-variant">
          Сумма реально сохранится — платёжного провайдера пока нет, деньги не списываются
        </span>
      </template>

      <template v-else-if="step === 'processing'">
        <div class="flex flex-col items-center gap-3 py-8">
          <span class="material-symbols-outlined text-primary text-[40px] animate-spin">sync</span>
          <span class="font-label-md text-label-md text-on-surface font-bold">Сохраняем взнос...</span>
        </div>
      </template>

      <template v-else>
        <div class="flex flex-col items-center gap-3 py-6 text-center">
          <span class="material-symbols-outlined text-secondary text-[48px]">check_circle</span>
          <span class="font-headline-sm text-headline-sm text-on-surface font-bold">Спасибо за поддержку!</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">
            {{ effectiveAmount }} ₽ добавлено к сбору отряда «{{ campaign?.squadName }}»
          </span>
          <button class="mt-2 px-5 py-2 rounded-full bg-surface-container text-on-surface font-label-md text-label-md font-bold" @click="close">
            Закрыть
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
