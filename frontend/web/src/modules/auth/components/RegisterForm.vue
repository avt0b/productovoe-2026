<script setup>
import { reactive, ref } from 'vue'

const emit = defineEmits(['success'])

const roles = [
  { id: 'researcher', label: 'Поисковик-исследователь' },
  { id: 'historian', label: 'Краевед / наставник' },
  { id: 'family', label: 'Родитель / семейный режим' },
]

const form = reactive({
  name: '',
  contact: '',
  role: 'family',
  password: '',
  passwordConfirm: '',
  agree: false,
})
const status = ref('idle')
const error = ref('')

function submit() {
  error.value = ''
  if (!form.name || !form.contact || !form.password) {
    error.value = 'Заполните ФИО, контакт и пароль'
    return
  }
  if (form.password !== form.passwordConfirm) {
    error.value = 'Пароли не совпадают'
    return
  }
  if (!form.agree) {
    error.value = 'Подтвердите согласие на обработку данных'
    return
  }
  status.value = 'pending'
  setTimeout(() => {
    status.value = 'done'
    emit('success')
  }, 900)
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="submit">
    <div>
      <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">ФИО</label>
      <input
        v-model="form.name"
        type="text"
        placeholder="Иванов Иван Иванович"
        class="w-full h-12 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
    </div>
    <div>
      <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
        Телефон или e-mail
      </label>
      <input
        v-model="form.contact"
        type="text"
        placeholder="+7 (900) 000-00-00 или you@mail.ru"
        class="w-full h-12 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
    </div>

    <div>
      <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1.5 font-bold">Роль</label>
      <div class="flex flex-col gap-2">
        <label
          v-for="role in roles"
          :key="role.id"
          class="flex items-center gap-3 p-3 rounded-DEFAULT bg-surface-container-low hover:bg-surface-container cursor-pointer transition-colors"
        >
          <input v-model="form.role" type="radio" :value="role.id" class="w-4 h-4 accent-primary cursor-pointer" />
          <span class="font-body-md text-body-md text-on-surface">{{ role.label }}</span>
        </label>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Пароль</label>
        <input
          v-model="form.password"
          type="password"
          placeholder="••••••••"
          class="w-full h-12 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
      </div>
      <div>
        <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
          Повтор пароля
        </label>
        <input
          v-model="form.passwordConfirm"
          type="password"
          placeholder="••••••••"
          class="w-full h-12 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
      </div>
    </div>

    <label class="flex items-start gap-2 cursor-pointer select-none">
      <input v-model="form.agree" type="checkbox" class="w-4 h-4 mt-0.5 rounded accent-primary cursor-pointer" />
      <span class="font-body-sm text-body-sm text-on-surface-variant">
        Согласен на обработку персональных данных и правила платформы «Маршруты победы»
      </span>
    </label>

    <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

    <button
      type="submit"
      class="h-12 rounded-full font-label-lg text-label-lg font-bold shadow-md transition-all flex items-center justify-center gap-2"
      :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary hover:opacity-95'"
      :disabled="status === 'pending'"
    >
      <span class="material-symbols-outlined text-[20px]" :class="{ 'animate-spin': status === 'pending' }">
        {{ status === 'done' ? 'check_circle' : status === 'pending' ? 'sync' : 'person_add' }}
      </span>
      <span>{{ status === 'done' ? 'Аккаунт создан' : status === 'pending' ? 'Создаём аккаунт...' : 'Создать аккаунт' }}</span>
    </button>
  </form>
</template>
