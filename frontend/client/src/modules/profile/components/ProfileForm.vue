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

const rows = computed(() => [
  { id: 'name', icon: 'badge', label: 'Как обращаться', value: props.profile.display_name || 'Не указано' },
  { id: 'city', icon: 'home_pin', label: 'Город', value: props.profile.city || 'Не указан' },
  { id: 'bio', icon: 'description', label: 'О себе', value: props.profile.bio || 'Пока ничего' },
])
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-end justify-between gap-space-sm">
      <div>
        <p class="font-archival text-archival uppercase text-on-surface-variant">Видно краеведам и командирам</p>
        <h2 class="font-headline-md text-headline-md text-on-surface">Данные исследователя</h2>
      </div>
      <button
        type="button"
        class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface transition-colors duration-200 active:scale-95"
        :aria-label="editing ? 'Отменить правку' : 'Изменить данные'"
        :aria-expanded="editing"
        @click="editing ? cancel() : (editing = true)"
      >
        <MsIcon :name="editing ? 'close' : 'edit'" :size="18" />
      </button>
    </div>

    <div class="rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="editing ? 'grid-rows-[0fr] opacity-0' : 'grid-rows-[1fr] opacity-100'"
        :inert="editing"
      >
        <dl class="flex flex-col gap-space-md overflow-hidden">
          <div v-for="row in rows" :key="row.id" class="flex items-start gap-space-sm">
            <MsIcon :name="row.icon" :size="20" class="mt-0.5 shrink-0 text-on-surface-variant" />
            <div class="min-w-0">
              <dt class="font-label-sm text-label-sm text-on-surface-variant">{{ row.label }}</dt>
              <dd class="whitespace-pre-line font-body-md text-body-md text-on-surface">{{ row.value }}</dd>
            </div>
          </div>
        </dl>
      </div>

      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="editing ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!editing"
      >
        <form class="flex flex-col gap-space-md overflow-hidden" @submit.prevent="save">
          <FormInput v-model="name" label="Как к вам обращаться" :maxlength="120" placeholder="Имя и фамилия" />
          <FormInput v-model="city" label="Город" :maxlength="120" placeholder="Орёл" />
          <FormTextarea v-model="bio" label="О себе" :maxlength="4000" placeholder="Чей подвиг ищете, в каком отряде, чем можете помочь" />

          <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

          <div class="flex items-center justify-end gap-space-xs">
            <button
              type="button"
              class="rounded-full px-space-md py-2 font-label-md text-label-md text-on-surface-variant active:scale-95"
              @click="cancel"
            >
              Отмена
            </button>
            <button
              type="submit"
              class="flex items-center gap-space-xs rounded-full bg-secondary px-space-md py-2 font-label-md text-label-md text-on-secondary active:scale-95 disabled:opacity-60"
              :disabled="!changed || saving"
            >
              <MsIcon :name="saving ? 'progress_activity' : 'save'" :size="18" :class="{ 'animate-spin': saving }" />
              Сохранить
            </button>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>
