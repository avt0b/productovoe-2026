<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { AVATAR_MAX_MB, updateProfile, uploadAvatar, type Profile } from '../data'

/**
 * Правка профиля: фото, имя, город, «о себе». Открывается кнопкой в карточке
 * исследователя — что человек видит в шапке, то здесь и меняет.
 */
const props = defineProps<{
  profile: Profile
  /** Имя из регистрации — подставляем, пока в профиле пусто. */
  fallbackName: string
}>()

const emit = defineEmits<{ saved: [profile: Profile]; close: [] }>()

const name = ref(props.profile.display_name || props.fallbackName)
const city = ref(props.profile.city)
const bio = ref(props.profile.bio)
/** Адрес фото в хранилище. `null` — без фото. */
const avatarUrl = ref<string | null>(props.profile.avatar_url)

const fileInput = ref<HTMLInputElement | null>(null)
/** Снимок с телефона, пока он грузится: смотреть на пустой круг незачем. */
const localPreview = ref<string | null>(null)
const uploading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const preview = computed(() => localPreview.value ?? avatarUrl.value)

const changed = computed(
  () =>
    name.value.trim() !== props.profile.display_name ||
    city.value.trim() !== props.profile.city ||
    bio.value.trim() !== props.profile.bio ||
    avatarUrl.value !== props.profile.avatar_url,
)

function dropPreview(): void {
  if (localPreview.value) URL.revokeObjectURL(localPreview.value)
  localPreview.value = null
}

/** Фото уходит в хранилище сразу после выбора: к «Сохранить» адрес уже готов. */
async function pick(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  dropPreview()
  localPreview.value = URL.createObjectURL(file)
  error.value = null
  uploading.value = true
  try {
    avatarUrl.value = await uploadAvatar(file)
  } catch (reason) {
    dropPreview()
    // 503 — хранилище фото не поднято (так бывает на стенде); остальное сохранится.
    error.value =
      reason instanceof ApiError && reason.status === 503
        ? 'Хранилище фото сейчас недоступно. Имя, город и «о себе» сохранятся и без снимка.'
        : errorText(reason)
  } finally {
    uploading.value = false
  }
}

function removePhoto(): void {
  dropPreview()
  avatarUrl.value = null
  error.value = null
}

async function save(): Promise<void> {
  if (!changed.value || saving.value || uploading.value) return
  saving.value = true
  error.value = null
  try {
    const saved = await updateProfile({
      display_name: name.value.trim(),
      city: city.value.trim(),
      bio: bio.value.trim(),
      avatar_url: avatarUrl.value,
    })
    emit('saved', saved)
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
  <SheetDialog title="Данные исследователя" subtitle="Фото, имя и «о себе» видят краеведы и командиры отрядов" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="save">
      <div class="flex items-center gap-space-md">
        <span
          class="relative flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-secondary-container text-on-secondary-container"
        >
          <img v-if="preview" :src="preview" alt="" class="h-full w-full object-cover" :class="{ 'opacity-50': uploading }" />
          <MsIcon v-else name="person" :size="32" />
          <MsIcon v-if="uploading" name="progress_activity" :size="24" class="absolute animate-spin" />
        </span>

        <div class="flex min-w-0 flex-col items-start gap-space-xs">
          <button
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
            :disabled="uploading"
            @click="fileInput?.click()"
          >
            <MsIcon name="add_a_photo" :size="18" />
            {{ preview ? 'Заменить фото' : 'Выбрать фото' }}
          </button>
          <button
            v-if="preview"
            type="button"
            class="px-space-xs font-label-md text-label-md text-on-surface-variant active:scale-95"
            @click="removePhoto"
          >
            Убрать фото
          </button>
          <p class="font-body-sm text-body-sm text-on-surface-variant">JPEG, PNG или WebP, до {{ AVATAR_MAX_MB }} МБ</p>
        </div>
      </div>
      <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" tabindex="-1" @change="pick" />

      <FormInput v-model="name" label="Как к вам обращаться" icon="badge" :maxlength="120" placeholder="Имя и фамилия" />
      <FormInput v-model="city" label="Город" icon="home_pin" :maxlength="120" placeholder="Орёл" />
      <FormTextarea
        v-model="bio"
        label="О себе"
        :rows="4"
        :maxlength="4000"
        placeholder="Чей подвиг ищете, в каком отряде, чем можете помочь"
      />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="!changed || saving || uploading"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'save'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>Сохранить</span>
      </button>
    </form>
  </SheetDialog>
</template>
