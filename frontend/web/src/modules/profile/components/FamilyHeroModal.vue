<script setup>
import { reactive, ref, watch } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as profileApi from '../api.js'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // null — новая карточка; иначе редактируем/удаляем существующего героя.
  hero: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved', 'deleted'])

const { session } = useAuthSession()

const STATUS_OPTIONS = [
  { id: 'veteran', label: 'Ветеран — дожил до Победы' },
  { id: 'killed_in_action', label: 'Погиб в бою' },
  { id: 'missing_in_action', label: 'Пропал без вести' },
  { id: 'died_of_wounds', label: 'Умер от ран' },
]

const form = reactive({ name: '', status: 'veteran', birthYear: '', deathYear: '', unit: '', note: '' })
const photoFile = ref(null)
const status = ref('idle') // idle | saving | deleting
const error = ref('')

// Backend (FamilyHeroCreate) допускает 1850..2100, но год позже текущего для
// исторической личности всегда ошибка — проверяем это на фронте, чтобы не
// ждать ответа сервера ради опечатки.
const CURRENT_YEAR = new Date().getFullYear()
const MIN_YEAR = 1850

function validate() {
  if (!form.name.trim()) return 'Укажите имя'
  const birth = form.birthYear ? Number(form.birthYear) : null
  const death = form.deathYear ? Number(form.deathYear) : null
  for (const [label, year] of [
    ['Год рождения', birth],
    ['Год смерти', death],
  ]) {
    if (year === null) continue
    if (!Number.isInteger(year) || year < MIN_YEAR || year > CURRENT_YEAR) {
      return `${label}: укажите год между ${MIN_YEAR} и ${CURRENT_YEAR}`
    }
  }
  if (birth !== null && death !== null && death < birth) {
    return 'Год смерти не может быть раньше года рождения'
  }
  return ''
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    error.value = ''
    photoFile.value = null
    status.value = 'idle'
    if (props.hero) {
      form.name = props.hero.name
      form.status = props.hero.status
      form.birthYear = props.hero.birth_year ?? ''
      form.deathYear = props.hero.death_year ?? ''
      form.unit = props.hero.unit
      form.note = props.hero.note
    } else {
      form.name = ''
      form.status = 'veteran'
      form.birthYear = ''
      form.deathYear = ''
      form.unit = ''
      form.note = ''
    }
  },
)

function close() {
  emit('update:modelValue', false)
}

function onPhotoChange(event) {
  photoFile.value = event.target.files?.[0] ?? null
}

async function submit() {
  const validationError = validate()
  if (validationError) {
    error.value = validationError
    return
  }
  error.value = ''
  status.value = 'saving'
  try {
    let photoUrl
    if (photoFile.value) {
      const { url } = await profileApi.uploadFamilyHeroPhoto(session.accessToken, photoFile.value)
      photoUrl = url
    }
    const payload = {
      name: form.name.trim(),
      status: form.status,
      birth_year: form.birthYear ? Number(form.birthYear) : null,
      death_year: form.deathYear ? Number(form.deathYear) : null,
      unit: form.unit.trim(),
      note: form.note.trim(),
      ...(photoUrl ? { photo_url: photoUrl } : {}),
    }
    const saved = props.hero
      ? await profileApi.updateFamilyHero(session.accessToken, props.hero.id, payload)
      : await profileApi.createFamilyHero(session.accessToken, payload)
    emit('saved', saved)
    close()
  } catch (err) {
    error.value = err.detail ?? 'Не удалось сохранить'
  } finally {
    status.value = 'idle'
  }
}

async function remove() {
  if (!props.hero) return
  status.value = 'deleting'
  error.value = ''
  try {
    await profileApi.deleteFamilyHero(session.accessToken, props.hero.id)
    emit('deleted', props.hero.id)
    close()
  } catch (err) {
    error.value = err.detail ?? 'Не удалось удалить'
    status.value = 'idle'
  }
}
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-2xl max-w-md w-full shadow-sheet flex flex-col max-h-[90vh] overflow-hidden">
      <div class="flex items-center justify-between p-5 border-b border-surface-container-high shrink-0">
        <span class="font-headline-sm text-headline-sm text-on-surface font-bold">
          {{ hero ? 'Изменить героя рода' : 'Добавить предка' }}
        </span>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <form class="p-5 flex flex-col gap-3 overflow-y-auto" @submit.prevent="submit">
        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Имя</label>
          <input
            v-model="form.name"
            type="text"
            placeholder="Сержант Воронов А. Г."
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>

        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Судьба</label>
          <select
            v-model="form.status"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          >
            <option v-for="opt in STATUS_OPTIONS" :key="opt.id" :value="opt.id">{{ opt.label }}</option>
          </select>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Год рождения</label>
            <input
              v-model="form.birthYear"
              type="number"
              :min="MIN_YEAR"
              :max="CURRENT_YEAR"
              placeholder="1919"
              class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
            />
          </div>
          <div>
            <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Год смерти</label>
            <input
              v-model="form.deathYear"
              type="number"
              :min="form.birthYear || MIN_YEAR"
              :max="CURRENT_YEAR"
              placeholder="1944"
              class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
            />
          </div>
        </div>

        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Часть</label>
          <input
            v-model="form.unit"
            type="text"
            placeholder="120-й стрелковый полк, Орловский рубеж"
            class="w-full h-11 px-4 rounded-full bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors"
          />
        </div>

        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Заметка</label>
          <textarea
            v-model="form.note"
            rows="2"
            placeholder="Подтверждено в ОБД «Мемориал», награды и т.п."
            class="w-full px-4 py-3 rounded-DEFAULT bg-surface-container-low font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
          />
        </div>

        <div>
          <label class="block font-label-sm text-label-sm text-on-surface-variant uppercase mb-1 font-bold">Фото</label>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="w-full font-body-sm text-body-sm text-on-surface-variant file:mr-3 file:px-4 file:py-2 file:rounded-full file:border-0 file:bg-secondary file:text-on-secondary file:font-label-sm file:text-label-sm file:font-bold"
            @change="onPhotoChange"
          />
        </div>

        <p v-if="error" class="font-label-sm text-label-sm text-error font-bold">{{ error }}</p>

        <div class="pt-2 flex items-center justify-between gap-3">
          <button
            v-if="hero"
            type="button"
            class="px-4 py-2.5 rounded-full bg-error-container text-on-error-container font-label-md text-label-md font-bold flex items-center gap-1.5 disabled:opacity-60"
            :disabled="status !== 'idle'"
            @click="remove"
          >
            <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': status === 'deleting' }">
              {{ status === 'deleting' ? 'sync' : 'delete' }}
            </span>
            Удалить
          </button>
          <span v-else />
          <button
            type="submit"
            class="px-6 py-2.5 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm flex items-center gap-2 disabled:opacity-60"
            :disabled="status !== 'idle'"
          >
            <span class="material-symbols-outlined text-[18px]" :class="{ 'animate-spin': status === 'saving' }">
              {{ status === 'saving' ? 'sync' : 'save' }}
            </span>
            {{ status === 'saving' ? 'Сохраняем...' : 'Сохранить' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
