<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthSession, roleLabel } from '@modules/auth'
import * as api from '../api.js'

const { session } = useAuthSession()

// Совпадает с SQUAD_CREATOR_ROLES в search_hq_service/services/permissions.py —
// это ровно те роли, кому бэкенд разрешит POST /squads, is_root не связан с полем role.
const ALLOWED_ROLES = ['searcher', 'moderator']

const canRegister = computed(
  () => session.user?.is_root || ALLOWED_ROLES.includes(session.user?.role),
)

const form = reactive({ name: '', region: '', description: '', contact: '' })
const status = ref('idle') // idle | pending | done
const error = ref('')
const mySquads = ref([])
const loadStatus = ref('idle')

async function loadMine() {
  if (session.status !== 'authenticated') return
  loadStatus.value = 'loading'
  try {
    mySquads.value = await api.listMySquads(session.accessToken, session.user.id)
    loadStatus.value = 'loaded'
  } catch {
    loadStatus.value = 'error'
  }
}

onMounted(loadMine)

async function submit() {
  error.value = ''
  if (!form.name.trim()) {
    error.value = 'Укажите название отряда'
    return
  }
  status.value = 'pending'
  try {
    const squad = await api.createSquad(session.accessToken, {
      name: form.name.trim(),
      region: form.region.trim(),
      description: form.description.trim(),
      contact: form.contact.trim(),
    })
    mySquads.value.unshift(squad)
    form.name = ''
    form.region = ''
    form.description = ''
    form.contact = ''
    status.value = 'done'
    setTimeout(() => (status.value = 'idle'), 1200)
  } catch (err) {
    status.value = 'idle'
    error.value = err.detail ?? 'Не удалось зарегистрировать отряд'
  }
}
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-5">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-primary text-[22px]">groups</span>
      <div class="flex flex-col">
        <span class="font-headline-sm text-headline-sm text-on-surface">Регистрация поискового отряда</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Заявка уходит напрямую в search_hq_service — вы сразу становитесь командиром отряда
          (Squad.leader_id)
        </span>
      </div>
    </div>

    <p v-if="session.status !== 'authenticated'" class="font-body-md text-body-md text-on-surface-variant">
      Войдите, чтобы зарегистрировать отряд.
    </p>

    <p v-else-if="!canRegister" class="font-body-md text-body-md text-on-surface-variant">
      Регистрировать отряды может пользователь с ролью «Поисковик-исследователь» или модератор.
      Ваша текущая роль — «{{ roleLabel(session.user?.role) }}»: бэкенд отклонит создание отряда
      с ней (<code class="font-mono text-label-sm">403 Создавать отряды могут поисковики и модераторы</code>).
    </p>

    <form v-else class="grid grid-cols-1 md:grid-cols-2 gap-3" @submit.prevent="submit">
      <input
        v-model="form.name"
        type="text"
        placeholder="Название отряда, например «Высота»"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors md:col-span-2"
      />
      <input
        v-model="form.region"
        type="text"
        placeholder="Регион, например Орловская область"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
      <input
        v-model="form.contact"
        type="text"
        placeholder="Контакт: телефон, telegram или e-mail"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
      <textarea
        v-model="form.description"
        rows="3"
        placeholder="Чем занимается отряд, опыт экспедиций"
        class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none md:col-span-2"
      />

      <p v-if="error" class="font-label-sm text-label-sm text-error font-bold md:col-span-2">{{ error }}</p>

      <button
        type="submit"
        class="h-11 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2 self-start px-6 md:col-span-2"
        :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
        :disabled="status === 'pending'"
      >
        <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': status === 'pending' }">
          {{ status === 'done' ? 'check_circle' : status === 'pending' ? 'sync' : 'flag' }}
        </span>
        <span>{{ status === 'done' ? 'Отряд зарегистрирован' : status === 'pending' ? 'Регистрируем...' : 'Зарегистрировать отряд' }}</span>
      </button>
    </form>

    <div v-if="session.status === 'authenticated' && mySquads.length" class="flex flex-col gap-2 pt-3 border-t border-surface-container-high">
      <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Мои отряды</span>
      <div
        v-for="squad in mySquads"
        :key="squad.id"
        class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-center justify-between gap-3"
      >
        <div class="flex flex-col min-w-0">
          <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ squad.name }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant truncate">{{ squad.region || 'Регион не указан' }}</span>
        </div>
        <span class="material-symbols-outlined text-secondary text-[20px] shrink-0">military_tech</span>
      </div>
    </div>
  </div>
</template>
