<script setup>
import { ref, computed } from 'vue'

const checklist = ref([
  { label: 'Резиновые сапоги (высокие)', checked: true },
  { label: 'Заряженный телефон с оффлайн-картами', checked: true },
  { label: 'Плотные рабочие перчатки', checked: false },
  { label: 'Термос с чаем и сухой паек', checked: false },
])

const checkedCount = computed(() => checklist.value.filter((item) => item.checked).length)

const enrollState = ref('idle')

function enroll() {
  if (enrollState.value !== 'idle') return
  enrollState.value = 'pending'
  setTimeout(() => {
    enrollState.value = 'done'
  }, 900)
}
</script>

<template>
  <div class="bg-secondary rounded-lg p-7 text-on-secondary shadow-lg relative overflow-hidden flex flex-col gap-6">
    <div class="absolute -right-20 -bottom-20 w-80 h-80 rounded-full bg-on-secondary-fixed/10 blur-2xl pointer-events-none" />

    <div class="flex items-center justify-between z-10">
      <div class="flex items-center gap-2 bg-secondary-fixed text-on-secondary-fixed px-3 py-1 rounded-full font-label-sm text-label-sm font-bold">
        <span class="material-symbols-outlined text-[16px]">school</span>
        <span>Полевая школа</span>
      </div>
      <span class="text-secondary-fixed-dim font-label-sm text-label-sm uppercase tracking-wider">Сессия #4</span>
    </div>

    <div class="flex flex-col gap-2 z-10">
      <h2 class="font-headline-lg text-headline-lg text-on-secondary font-extrabold leading-tight">
        Выходные с поисковиком
      </h2>
      <p class="font-body-md text-body-md text-secondary-fixed-dim">
        Однодневный ознакомительный выезд для тех, кто хочет прикоснуться к живой истории и помочь экспедиции.
      </p>
    </div>

    <div class="bg-on-secondary-fixed/30 rounded-DEFAULT p-4 flex flex-col gap-3 backdrop-blur-sm z-10">
      <div class="flex items-start gap-3">
        <span class="material-symbols-outlined text-tertiary-fixed text-[22px] shrink-0 mt-0.5">event</span>
        <div>
          <span class="font-label-lg text-label-lg text-on-secondary font-bold block">Суббота, 14 сентября</span>
          <span class="font-body-sm text-body-sm text-secondary-fixed-dim">
            Разведка у села Крупышино: археология и топография
          </span>
        </div>
      </div>
      <div class="flex items-center gap-3 pt-2">
        <div class="w-10 h-10 rounded-full bg-secondary-fixed flex items-center justify-center text-on-secondary-fixed font-bold shrink-0">
          <span class="material-symbols-outlined text-[20px]">explore</span>
        </div>
        <div class="flex flex-col">
          <span class="font-label-md text-label-md text-on-secondary font-bold">Михаил Смирнов</span>
          <span class="font-label-sm text-label-sm text-secondary-fixed-dim">Руководитель выезда • Стаж 18 лет</span>
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-3 z-10">
      <div class="flex items-center justify-between">
        <span class="font-label-lg text-label-lg text-on-secondary font-bold">Чек-лист новичка</span>
        <span class="font-label-sm text-label-sm text-tertiary-fixed font-bold">{{ checkedCount }} из {{ checklist.length }} готово</span>
      </div>
      <div class="flex flex-col gap-2.5">
        <label
          v-for="item in checklist"
          :key="item.label"
          class="flex items-center gap-3 p-2.5 rounded-DEFAULT bg-on-secondary-fixed/20 hover:bg-on-secondary-fixed/30 cursor-pointer transition-colors select-none"
        >
          <input v-model="item.checked" type="checkbox" class="w-5 h-5 rounded accent-tertiary-fixed cursor-pointer" />
          <span class="font-body-md text-body-md text-on-secondary flex-1">{{ item.label }}</span>
        </label>
      </div>
    </div>

    <div class="flex items-center justify-between p-3 rounded-DEFAULT bg-secondary-fixed/15 z-10">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-tertiary-fixed animate-ping" />
        <span class="font-label-md text-label-md text-tertiary-fixed font-bold">Осталось 4 места из 15</span>
      </div>
      <span class="font-label-sm text-label-sm text-secondary-fixed-dim">Участие бесплатное</span>
    </div>

    <div class="flex flex-col gap-3 pt-2 z-10">
      <button
        class="w-full py-4 px-6 rounded-full font-label-lg text-label-lg font-bold shadow-md hover:scale-[0.99] transition-all flex items-center justify-center gap-2"
        :class="
          enrollState === 'done'
            ? 'bg-secondary-fixed text-on-secondary-fixed'
            : 'bg-tertiary-fixed hover:bg-tertiary-fixed-dim text-on-tertiary-fixed'
        "
        :disabled="enrollState !== 'idle'"
        @click="enroll"
      >
        <span
          class="material-symbols-outlined text-[20px]"
          :class="{ 'animate-spin': enrollState === 'pending' }"
        >
          {{ enrollState === 'done' ? 'check_circle' : enrollState === 'pending' ? 'sync' : 'how_to_reg' }}
        </span>
        <span>
          {{
            enrollState === 'done'
              ? 'Вы в списке группы!'
              : enrollState === 'pending'
                ? 'Заявка обрабатывается...'
                : 'Записаться волонтером'
          }}
        </span>
      </button>
      <a
        href="#"
        class="flex items-center justify-center gap-1.5 py-2 text-secondary-fixed-dim hover:text-on-secondary font-label-md text-label-md transition-colors"
      >
        <span class="material-symbols-outlined text-[18px]">picture_as_pdf</span>
        <span class="underline underline-offset-4">Памятка новичка (PDF, 2.4 МБ)</span>
      </a>
    </div>
  </div>
</template>
