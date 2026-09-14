<script setup>
import { reactive, ref } from 'vue'

const notes = ref([
  {
    title: 'Памятник морякам Тихоокеанского флота у с. Крупышино',
    author: 'Краевед Л. Панкратова',
    status: 'verified',
  },
  {
    title: 'Воспоминание местного жителя о посадке самолёта эскадрильи «Нормандия — Неман»',
    author: 'Житель д. Апальково, передано отряду «Костёр»',
    status: 'pending',
  },
])

const statusMeta = {
  verified: { label: 'Подтверждено', class: 'bg-secondary-fixed text-on-secondary-fixed', icon: 'verified' },
  pending: { label: 'На проверке', class: 'bg-tertiary-fixed text-on-tertiary-fixed', icon: 'hourglass_top' },
}

const formOpen = ref(false)
const submitted = ref(false)
const form = reactive({ title: '', text: '' })

function submit() {
  if (!form.title) return
  notes.value.unshift({ title: form.title, author: 'Вы (ожидает верификации краеведа)', status: 'pending' })
  submitted.value = true
  form.title = ''
  form.text = ''
  setTimeout(() => {
    formOpen.value = false
    submitted.value = false
  }, 1200)
}
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-5">
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-2.5">
        <span class="material-symbols-outlined text-secondary text-[22px]">groups</span>
        <div class="flex flex-col">
          <span class="font-headline-sm text-headline-sm text-on-surface">Народный архив</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">
            Любой может предложить событие — краевед или поисковой отряд его подтверждает
          </span>
        </div>
      </div>
      <button
        class="px-4 py-2 rounded-full bg-secondary-fixed hover:bg-secondary-fixed-dim text-on-secondary-fixed font-label-md text-label-md font-bold flex items-center gap-1.5 shadow-sm transition-all"
        @click="formOpen = !formOpen"
      >
        <span class="material-symbols-outlined text-[18px]">add</span>
        <span>Предложить событие</span>
      </button>
    </div>

    <div v-if="formOpen" class="bg-surface-container-low rounded-DEFAULT p-4 flex flex-col gap-3">
      <template v-if="!submitted">
        <input
          v-model="form.title"
          type="text"
          placeholder="Название события или объекта"
          class="w-full h-11 px-4 rounded-full bg-surface-container-lowest font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
        <textarea
          v-model="form.text"
          rows="3"
          placeholder="Что произошло, кто рассказал, есть ли фото или документы"
          class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-lowest font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
        />
        <button
          class="self-end px-5 py-2 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm"
          @click="submit"
        >
          Отправить на проверку
        </button>
      </template>
      <div v-else class="flex items-center gap-2 text-secondary font-label-md text-label-md font-bold py-2">
        <span class="material-symbols-outlined text-[20px]">check_circle</span>
        Событие отправлено краеведу на верификацию
      </div>
    </div>

    <div class="flex flex-col gap-2.5">
      <div
        v-for="note in notes"
        :key="note.title"
        class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-center justify-between gap-3"
      >
        <div class="flex flex-col min-w-0">
          <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ note.title }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant">{{ note.author }}</span>
        </div>
        <span
          class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-bold flex items-center gap-1 shrink-0"
          :class="statusMeta[note.status].class"
        >
          <span class="material-symbols-outlined text-[14px]">{{ statusMeta[note.status].icon }}</span>
          {{ statusMeta[note.status].label }}
        </span>
      </div>
    </div>
  </div>
</template>
