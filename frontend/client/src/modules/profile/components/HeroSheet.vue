<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import {
  AVATAR_MAX_MB,
  HERO_STATUS,
  HERO_STATUS_ORDER,
  createHero,
  deleteHero,
  updateHero,
  uploadAvatar,
  type FamilyHero,
  type HeroStatus,
} from '../data'

/**
 * Герой семейного древа: прадед, прабабушка, любой родной, кого помнят.
 *
 * Древо приватное — его видит только владелец профиля. В народный архив герой
 * попадает отдельно, карточкой бойца: там его проверяет краевед.
 */
const props = withDefaults(defineProps<{ hero?: FamilyHero | null }>(), { hero: null })

const emit = defineEmits<{ close: []; saved: []; removed: [] }>()

const statusOptions = HERO_STATUS_ORDER.map((value) => ({ value, title: HERO_STATUS[value].title }))

const name = ref(props.hero?.name ?? '')
const status = ref<HeroStatus>(props.hero?.status ?? 'veteran')
const birthYear = ref<number | null>(props.hero?.birth_year ?? null)
const deathYear = ref<number | null>(props.hero?.death_year ?? null)
const unit = ref(props.hero?.unit ?? '')
const note = ref(props.hero?.note ?? '')
const photoUrl = ref<string | null>(props.hero?.photo_url ?? null)

const fileInput = ref<HTMLInputElement | null>(null)
const localPreview = ref<string | null>(null)
const uploading = ref(false)
const saving = ref(false)
const confirmingDelete = ref(false)
const error = ref<string | null>(null)

const photo = computed(() => localPreview.value ?? photoUrl.value)

const missing = computed(() => {
  if (!name.value.trim()) return 'Как звали героя?'
  const birth = birthYear.value
  const death = deathYear.value
  if (birth !== null && death !== null && death < birth) return 'Год гибели раньше года рождения — проверьте даты'
  return null
})

function dropPreview(): void {
  if (localPreview.value) URL.revokeObjectURL(localPreview.value)
  localPreview.value = null
}

/** Снимок уходит в хранилище сразу: к «Сохранить» адрес уже готов. */
async function pickPhoto(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  dropPreview()
  localPreview.value = URL.createObjectURL(file)
  error.value = null
  uploading.value = true
  try {
    photoUrl.value = await uploadAvatar(file)
  } catch (reason) {
    dropPreview()
    // 503 — хранилище фото не поднято; имя и судьба сохранятся и без снимка.
    error.value =
      reason instanceof ApiError && reason.status === 503
        ? 'Хранилище фото сейчас недоступно. Сохраните героя без снимка — добавите позже.'
        : errorText(reason)
  } finally {
    uploading.value = false
  }
}

function removePhoto(): void {
  dropPreview()
  photoUrl.value = null
  error.value = null
}

async function save(): Promise<void> {
  if (missing.value || saving.value || uploading.value) return
  saving.value = true
  error.value = null
  const draft = {
    name: name.value.trim(),
    status: status.value,
    birth_year: birthYear.value === null ? null : Math.round(birthYear.value),
    death_year: deathYear.value === null ? null : Math.round(deathYear.value),
    unit: unit.value.trim(),
    note: note.value.trim(),
    photo_url: photoUrl.value,
    archive_entry_id: props.hero?.archive_entry_id ?? null,
  }
  try {
    if (props.hero) await updateHero(props.hero.id, draft)
    else await createHero(draft)
    emit('saved')
    emit('close')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

async function remove(): Promise<void> {
  const hero = props.hero
  if (!hero || saving.value) return
  saving.value = true
  error.value = null
  try {
    await deleteHero(hero.id)
    emit('removed')
    emit('close')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

onBeforeUnmount(dropPreview)
</script>

<template>
  <SheetDialog
    :title="hero ? 'Герой семьи' : 'Новый герой семьи'"
    subtitle="Древо видите только вы — в народный архив герой попадает отдельно"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-md" @submit.prevent="save">
      <div class="flex items-center gap-space-md">
        <span
          class="relative flex h-20 w-16 shrink-0 items-center justify-center overflow-hidden rounded-DEFAULT bg-surface-container-low text-on-surface-variant"
        >
          <img v-if="photo" :src="photo" alt="" class="h-full w-full object-cover" :class="{ 'opacity-50': uploading }" />
          <MsIcon v-else name="person" :size="28" />
          <MsIcon v-if="uploading" name="progress_activity" :size="20" class="absolute animate-spin" />
        </span>
        <div class="flex min-w-0 flex-col items-start gap-space-xs">
          <button
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
            :disabled="uploading"
            @click="fileInput?.click()"
          >
            <MsIcon name="add_a_photo" :size="18" />
            {{ photo ? 'Заменить снимок' : 'Фото героя' }}
          </button>
          <button
            v-if="photo"
            type="button"
            class="px-space-xs font-label-md text-label-md text-on-surface-variant active:scale-95"
            @click="removePhoto"
          >
            Убрать снимок
          </button>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Необязательно, JPEG, PNG или WebP, до {{ AVATAR_MAX_MB }} МБ
          </p>
        </div>
      </div>
      <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" tabindex="-1" @change="pickPhoto" />

      <FormInput v-model="name" label="Имя" icon="badge" :maxlength="255" placeholder="Воронов Алексей Григорьевич" required />
      <FormSelect v-model="status" label="Судьба" :options="statusOptions" icon="military_tech" />
      <div class="grid grid-cols-2 gap-space-sm">
        <FormInput v-model="birthYear" label="Год рождения" type="number" inputmode="numeric" :min="1850" :max="2100" placeholder="1920" />
        <FormInput v-model="deathYear" label="Год гибели" type="number" inputmode="numeric" :min="1850" :max="2100" placeholder="1943" />
      </div>
      <FormInput v-model="unit" label="Часть" icon="flag" :maxlength="300" placeholder="308-я стрелковая дивизия" />
      <FormTextarea
        v-model="note"
        label="Что о нём знают в семье"
        :rows="3"
        :maxlength="1000"
        placeholder="Где воевал, как вспоминают дома, что сохранилось: письма, награды, фотографии"
      />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving || uploading"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'save'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ hero ? 'Сохранить' : 'Добавить в древо' }}</span>
      </button>

      <!-- Убрать героя — в два нажатия: это семейная память, случайный тап её не сотрёт. -->
      <template v-if="hero">
        <button
          type="button"
          class="self-center rounded-full px-space-md py-2 font-label-md text-label-md text-error active:scale-95"
          :aria-expanded="confirmingDelete"
          @click="confirmingDelete = !confirmingDelete"
        >
          Убрать из древа
        </button>
        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="confirmingDelete ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          :inert="!confirmingDelete"
        >
          <div class="overflow-hidden">
            <div
              class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-low p-space-md"
              role="alertdialog"
              aria-label="Подтверждение удаления героя"
            >
              <p class="font-body-sm text-body-sm text-on-surface">
                Убрать героя из семейного древа? Запись в народном архиве, если она есть, останется.
              </p>
              <div class="flex gap-space-sm">
                <button
                  type="button"
                  class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
                  @click="confirmingDelete = false"
                >
                  Оставить
                </button>
                <button
                  type="button"
                  class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error active:scale-95 disabled:opacity-60"
                  :disabled="saving"
                  @click="remove"
                >
                  <MsIcon name="delete" :size="18" />
                  Убрать
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </form>
  </SheetDialog>
</template>
