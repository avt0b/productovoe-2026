<script setup>
import { reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import { useProfileStore } from '../profileStore.js'

const { session } = useAuthSession()
const { profile, saveMyProfile } = useProfileStore()

const form = reactive({
  fullName: '',
  phone: '+7 (920) 814-22-90',
  city: '',
  bio: '',
})
const status = ref('idle')
const error = ref('')

watch(
  () => profile.data,
  (data) => {
    if (!data) return
    form.fullName = data.display_name
    form.city = data.city
    form.bio = data.bio
  },
  { immediate: true },
)

async function onSubmit() {
  if (session.status !== 'authenticated') {
    error.value = 'Войдите, чтобы сохранить профиль'
    return
  }
  status.value = 'pending'
  error.value = ''
  try {
    // squad_id ждёт связки с search_hq_service (список реальных отрядов), а
    // "Телефон" вообще не хранится в user_service — поля остаются в форме
    // для UX, но на бэкенд не уходят, пока там нет соответствующих полей.
    await saveMyProfile({
      display_name: form.fullName || undefined,
      city: form.city || undefined,
      bio: form.bio || undefined,
    })
    status.value = 'done'
    setTimeout(() => (status.value = 'idle'), 1500)
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось сохранить профиль'
  }
}
</script>

<template>
  <div class="bg-surface-container-lowest p-6 rounded-DEFAULT shadow-sm flex flex-col">
    <div class="flex items-center gap-3 mb-6">
      <div class="w-10 h-10 rounded-full bg-surface-container-high text-on-surface flex items-center justify-center">
        <span class="material-symbols-outlined text-[20px]">badge</span>
      </div>
      <div class="flex flex-col">
        <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Данные исследователя</h2>
        <span class="font-body-sm text-body-sm text-on-surface-variant">Связь со штабом экспедиции</span>
      </div>
    </div>

    <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <div>
        <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
          ФИО исследователя
        </label>
        <input
          v-model="form.fullName"
          type="text"
          placeholder="Иванов Иван Иванович"
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Телефон штаба <span class="normal-case font-normal text-on-surface-variant/70">(пока не хранится)</span>
          </label>
          <input
            v-model="form.phone"
            type="tel"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Город базирования
          </label>
          <input
            v-model="form.city"
            type="text"
            placeholder="г. Орёл"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>
      </div>

      <div>
        <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">О себе</label>
        <textarea
          v-model="form.bio"
          rows="3"
          placeholder="Пара слов о вашей экспедиционной работе"
          class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
        />
      </div>

      <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

      <div class="pt-2 flex justify-end">
        <button
          type="submit"
          class="font-label-md text-label-md font-bold px-6 py-2.5 rounded-full transition-colors shadow-sm flex items-center gap-2"
          :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-secondary hover:bg-on-secondary-fixed-variant text-on-secondary'"
          :disabled="status === 'pending'"
        >
          <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': status === 'pending' }">
            {{ status === 'done' ? 'check_circle' : status === 'pending' ? 'sync' : 'save' }}
          </span>
          <span>{{ status === 'done' ? 'Сохранено' : status === 'pending' ? 'Сохраняем...' : 'Сохранить профиль' }}</span>
        </button>
      </div>
    </form>
  </div>
</template>
