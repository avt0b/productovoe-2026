<script setup>
import { reactive, ref } from 'vue'

const emit = defineEmits(['success'])

const form = reactive({ login: '', password: '', remember: true })
const status = ref('idle')
const error = ref('')

function submit() {
  error.value = ''
  if (!form.login || !form.password) {
    error.value = 'Заполните телефон/e-mail и пароль'
    return
  }
  status.value = 'pending'
  setTimeout(() => {
    status.value = 'done'
    emit('success')
  }, 800)
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="submit">
    <div>
      <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
        Телефон или e-mail
      </label>
      <input
        v-model="form.login"
        type="text"
        placeholder="+7 (900) 000-00-00 или you@mail.ru"
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
