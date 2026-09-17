<script setup>
import { reactive, ref } from 'vue'
import { useAuthSession } from '../session.js'

const emit = defineEmits(['success'])

const { login } = useAuthSession()

const form = reactive({ email: '', password: '', remember: true })
const status = ref('idle')
const error = ref('')

async function submit() {
  error.value = ''
  if (!form.email || !form.password) {
    error.value = 'Заполните e-mail и пароль'
    return
  }
  status.value = 'pending'
  try {
    await login({ email: form.email, password: form.password })
    status.value = 'done'
    emit('success')
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось войти. Проверьте e-mail и пароль'
  }
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="submit">
    <div>
      <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">E-mail</label>
      <input
        v-model="form.email"
        type="email"
        placeholder="you@mail.ru"
        class="w-full h-12 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
    </div>
    <div>
      <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Пароль</label>
      <input
        v-model="form.password"
        type="password"
        placeholder="••••••••"
        class="w-full h-12 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
    </div>

    <div class="flex items-center justify-between">
      <label class="flex items-center gap-2 cursor-pointer select-none">
        <input v-model="form.remember" type="checkbox" class="w-4 h-4 rounded accent-primary cursor-pointer" />
        <span class="font-body-sm text-body-sm text-on-surface-variant">Запомнить меня</span>
      </label>
      <a href="#" class="font-label-sm text-label-sm text-primary font-bold hover:underline">Забыли пароль?</a>
    </div>

    <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

    <button
      type="submit"
      class="h-12 rounded-full font-label-lg text-label-lg font-bold shadow-md transition-all flex items-center justify-center gap-2"
      :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary hover:opacity-95'"
      :disabled="status === 'pending'"
    >
      <span class="material-symbols-outlined text-[20px]" :class="{ 'animate-spin': status === 'pending' }">
        {{ status === 'done' ? 'check_circle' : status === 'pending' ? 'sync' : 'login' }}
      </span>
      <span>{{ status === 'done' ? 'Вход выполнен' : status === 'pending' ? 'Проверяем...' : 'Войти' }}</span>
    </button>
  </form>
</template>
