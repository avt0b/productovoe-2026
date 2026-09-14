<script setup>
import { reactive, ref } from 'vue'
import GuideRatingList from './GuideRatingList.vue'

const form = reactive({ org: '', groupSize: '', date: '' })
const submitted = ref(false)

function submit() {
  if (!form.org) return
  submitted.value = true
  setTimeout(() => {
    submitted.value = false
    form.org = ''
    form.groupSize = ''
    form.date = ''
  }, 1500)
}
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-6">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-primary text-[22px]">groups_3</span>
      <div class="flex flex-col">
        <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface flex items-center gap-2 flex-wrap">
          Заявки школ и клубов на экскурсии
          <span class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-bold normal-case">
            демо — модуль ещё не реализован в search_hq_service
          </span>
        </h2>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Выберите гида-поисковика или краеведа и оставьте заявку на групповой выезд
        </span>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
            Школа или клуб
          </label>
          <input
            v-model="form.org"
            type="text"
            placeholder="Например, школа № 12, г. Орёл"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
              Размер группы
            </label>
            <input
              v-model="form.groupSize"
              type="text"
              placeholder="15 человек"
              class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
            />
          </div>
          <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">
              Желаемая дата
            </label>
            <input
              v-model="form.date"
              type="date"
              class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
            />
          </div>
        </div>
        <button
          type="submit"
          class="mt-1 px-5 py-2.5 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2"
          :class="submitted ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
        >
          <span class="material-symbols-outlined text-[18px]">{{ submitted ? 'check_circle' : 'send' }}</span>
          <span>{{ submitted ? 'Заявка отправлена штабу' : 'Отправить заявку' }}</span>
        </button>
      </form>

      <div class="flex flex-col gap-2">
        <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Гиды с рейтингом</span>
        <GuideRatingList />
      </div>
    </div>
  </div>
</template>
