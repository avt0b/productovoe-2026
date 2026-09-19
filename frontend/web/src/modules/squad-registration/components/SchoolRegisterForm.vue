<script setup>
import { reactive, ref } from 'vue'
import { useSchoolRegistry } from '../schoolRegistry.js'

const { schools, addSchool } = useSchoolRegistry()

const KIND_OPTIONS = [
  { id: 'school', label: 'Школа' },
  { id: 'club', label: 'Клуб / кружок' },
  { id: 'other', label: 'Другое' },
]

const form = reactive({
  name: '',
  kind: 'school',
  city: '',
  contactPerson: '',
  phone: '',
  email: '',
  expectedGroupSize: '',
  comment: '',
  consent: false,
})
const status = ref('idle') // idle | done
const error = ref('')

function submit() {
  error.value = ''
  if (!form.name.trim()) {
    error.value = 'Укажите название школы или клуба'
    return
  }
  if (!form.contactPerson.trim() || !form.phone.trim()) {
    error.value = 'Укажите контактное лицо и телефон для связи'
    return
  }
  if (!form.consent) {
    error.value = 'Подтвердите согласие на обработку контактных данных'
    return
  }
  addSchool({
    name: form.name.trim(),
    kind: form.kind,
    city: form.city.trim(),
    contact_person: form.contactPerson.trim(),
    phone: form.phone.trim(),
    email: form.email.trim(),
    expected_group_size: form.expectedGroupSize ? Number(form.expectedGroupSize) : null,
    comment: form.comment.trim(),
  })
  form.name = ''
  form.city = ''
  form.contactPerson = ''
  form.phone = ''
  form.email = ''
  form.expectedGroupSize = ''
  form.comment = ''
  form.consent = false
  status.value = 'done'
  setTimeout(() => (status.value = 'idle'), 1500)
}
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col gap-5">
    <div class="flex items-center gap-2.5">
      <span class="material-symbols-outlined text-primary text-[22px]">school</span>
      <div class="flex flex-col">
        <h2 class="font-headline-sm text-headline-sm text-on-surface flex items-center gap-2 flex-wrap">
          Регистрация школы или клуба
          <span
            class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-bold normal-case"
          >
            демо — в search_hq_service нет такой сущности
          </span>
        </h2>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Заявка сохраняется только в этом браузере (localStorage), пока бэкенд не реализует
          ручку — контракт для неё описан в BACKEND_INTEGRATION.md
        </span>
      </div>
    </div>

    <form class="grid grid-cols-1 md:grid-cols-2 gap-3" @submit.prevent="submit">
      <input
        v-model="form.name"
        type="text"
        placeholder="Название, например школа № 12, г. Орёл"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors md:col-span-2"
      />
      <div class="flex flex-wrap gap-2 md:col-span-2">
        <button
          v-for="opt in KIND_OPTIONS"
          :key="opt.id"
          type="button"
          class="px-3 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all"
          :class="
            form.kind === opt.id
              ? 'bg-secondary text-on-secondary'
              : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
          "
          @click="form.kind = opt.id"
        >
          {{ opt.label }}
        </button>
      </div>
      <input
        v-model="form.city"
        type="text"
        placeholder="Город / регион"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
      <input
        v-model="form.expectedGroupSize"
        type="number"
        min="1"
        placeholder="Размер группы, чел."
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
      <input
        v-model="form.contactPerson"
        type="text"
        placeholder="Контактное лицо, ФИО"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
      <input
        v-model="form.phone"
        type="tel"
        placeholder="Телефон"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
      <input
        v-model="form.email"
        type="email"
        placeholder="E-mail (необязательно)"
        class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors md:col-span-2"
      />
      <textarea
        v-model="form.comment"
        rows="2"
        placeholder="Пожелания: классы, тема экскурсии, желаемые даты"
        class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none md:col-span-2"
      />

      <label class="flex items-start gap-2 cursor-pointer select-none md:col-span-2">
        <input v-model="form.consent" type="checkbox" class="w-4 h-4 mt-0.5 rounded accent-primary cursor-pointer" />
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Согласен(на) на обработку указанных контактных данных для связи по заявке
        </span>
      </label>

      <p v-if="error" class="font-label-sm text-label-sm text-error font-bold md:col-span-2">{{ error }}</p>

      <button
        type="submit"
        class="h-11 rounded-full font-label-md text-label-md font-bold shadow-sm transition-all flex items-center justify-center gap-2 self-start px-6 md:col-span-2"
        :class="status === 'done' ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
      >
        <span class="material-symbols-outlined text-[18px]">{{ status === 'done' ? 'check_circle' : 'send' }}</span>
        <span>{{ status === 'done' ? 'Заявка сохранена локально' : 'Зарегистрировать' }}</span>
      </button>
    </form>

    <div v-if="schools.length" class="flex flex-col gap-2 pt-3 border-t border-surface-container-high">
      <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">
        Сохранено в этом браузере
      </span>
      <div
        v-for="s in schools"
        :key="s.id"
        class="bg-surface-container-low p-3.5 rounded-DEFAULT flex items-center justify-between gap-3"
      >
        <div class="flex flex-col min-w-0">
          <span class="font-label-md text-label-md text-on-surface font-bold truncate">{{ s.name }}</span>
          <span class="font-body-sm text-body-sm text-on-surface-variant truncate">
            {{ s.contact_person }} · {{ s.phone }}
          </span>
        </div>
        <span class="px-2.5 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-bold shrink-0">
          {{ KIND_OPTIONS.find((k) => k.id === s.kind)?.label ?? s.kind }}
        </span>
      </div>
    </div>
  </div>
</template>
