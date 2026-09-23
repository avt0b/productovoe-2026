<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { updateProfile, type Profile } from '../data'

/** Данные исследователя из `user_service`: как обращаться, город, о себе. */
const props = defineProps<{
  profile: Profile
  /** Имя из регистрации — подсказка, пока в профиле пусто. */
  fallbackName: string
}>()

const emit = defineEmits<{ saved: [profile: Profile] }>()

const editing = ref(false)
const name = ref('')
const city = ref('')
const bio = ref('')
const saving = ref(false)
const error = ref<string | null>(null)

function reset(): void {
  name.value = props.profile.display_name || props.fallbackName
  city.value = props.profile.city
  bio.value = props.profile.bio
  error.value = null
}

watch(() => props.profile, reset, { immediate: true })

const changed = computed(
  () =>
    name.value.trim() !== props.profile.display_name ||
    city.value.trim() !== props.profile.city ||
    bio.value.trim() !== props.profile.bio,
)

async function save(): Promise<void> {
  if (!changed.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    const saved = await updateProfile({ display_name: name.value.trim(), city: city.value.trim(), bio: bio.value.trim() })
    editing.value = false
    emit('saved', saved)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

function cancel(): void {
  reset()
  editing.value = false
}
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-center justify-between px-1">
      <div>
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Данные исследователя</h3>
        <span class="font-body-sm text-body-sm text-on-surface-variant">Видны краеведам и командирам отрядов</span>
      </div>
      <button
        v-if="!editing"
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant hover:text-primary"
        aria-label="Изменить данные"
        @click="editing = true"
      >
        <MsIcon name="edit" :size="19" />
      </button>
    </div>

    <form v-if="editing" class="flex flex-col gap-space-md rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm" @submit.prevent="save">
      <FormInput v-model="name" label="Как к вам обращаться" :maxlength="120" placeholder="Имя и фамилия" />
      <FormInput v-model="city" label="Город" :maxlength="120" placeholder="Орёл" />
      <FormTextarea v-model="bio" label="О себе" :maxlength="4000" placeholder="Чей подвиг ищете, в каком отряде, чем можете помочь" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <div class="grid grid-cols-2 gap-space-sm">
        <button
          type="button"
          class="rounded-full bg-surface-container-high py-3 font-label-lg text-label-lg text-on-surface"
          @click="cancel"
        >
          Отмена
        </button>
        <button
          type="submit"
          class="flex items-center justify-center gap-1.5 rounded-full bg-primary py-3 font-label-lg text-label-lg text-on-primary disabled:opacity-60"
          :disabled="!changed || saving"
        >
          <MsIcon :name="saving ? 'progress_activity' : 'save'" :size="18" :class="{ 'animate-spin': saving }" />
          Сохранить
        </button>
      </div>
    </form>

    <dl v-else class="flex flex-col gap-space-md rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
      <div class="flex items-center gap-space-sm">
        <MsIcon name="badge" :size="20" class="shrink-0 text-on-surface-variant" />
        <div class="min-w-0">
          <dt class="font-label-sm text-label-sm text-outline">Как обращаться</dt>
          <dd class="truncate font-label-lg text-label-lg text-on-surface">{{ profile.display_name || 'Не указано' }}</dd>
        </div>
      </div>
      <div class="flex items-center gap-space-sm">
        <MsIcon name="home_pin" :size="20" class="shrink-0 text-on-surface-variant" />
        <div class="min-w-0">
          <dt class="font-label-sm text-label-sm text-outline">Город</dt>
          <dd class="truncate font-label-lg text-label-lg text-on-surface">{{ profile.city || 'Не указан' }}</dd>
        </div>
      </div>
      <div class="flex items-start gap-space-sm">
        <MsIcon name="description" :size="20" class="mt-0.5 shrink-0 text-on-surface-variant" />
        <div class="min-w-0">
          <dt class="font-label-sm text-label-sm text-outline">О себе</dt>
          <dd class="whitespace-pre-line font-body-sm text-body-sm text-on-surface">{{ profile.bio || 'Пока ничего' }}</dd>
        </div>
      </div>
    </dl>
  </section>
</template>
