<script setup>
import { reactive } from 'vue'

const form = reactive({
  fullName: 'Константин Павлович Смирнов',
  phone: '+7 (920) 814-22-90',
  city: 'г. Орёл',
  squad: 'Сводный поисковый отряд «Высота»',
})

function onSubmit() {
  // TODO: persist profile changes
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
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Телефон штаба
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
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>
      </div>

      <div>
        <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
          Поисковый отряд
        </label>
        <input
          v-model="form.squad"
          type="text"
          class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
        />
      </div>

      <div class="pt-2 flex justify-end">
        <button
          type="submit"
          class="bg-secondary hover:bg-on-secondary-fixed-variant text-on-secondary font-label-md text-label-md font-bold px-6 py-2.5 rounded-full transition-colors shadow-sm flex items-center gap-2"
        >
          <span class="material-symbols-outlined text-[18px]">save</span>
          <span>Сохранить профиль</span>
        </button>
      </div>
    </form>
  </div>
</template>
