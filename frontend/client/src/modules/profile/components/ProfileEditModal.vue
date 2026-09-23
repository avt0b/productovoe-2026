<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, useId } from 'vue'

import { errorText } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'

import { updateMyProfile, uploadAvatar, type Profile } from '../api'

const props = defineProps<{ profile: Profile }>()

const emit = defineEmits<{ close: []; saved: [profile: Profile] }>()

/** Правим копию: закрытие без сохранения не должно менять карточку под окном. */
const displayName = ref(props.profile.display_name)
/**
 * Предел «О себе» — свой, не серверный: `user_service` принимает до 4000
 * символов, но такой текст превращает карточку профиля в стену. Триста
 * укладываются примерно в пять строк.
 */
const BIO_LIMIT = 300

const bio = ref(props.profile.bio.slice(0, BIO_LIMIT))
const avatarUrl = ref(props.profile.avatar_url)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const subscribed = ref(props.profile.subscribed_to_search)
const radius = ref(props.profile.alert_radius_km)

const bioLeft = computed(() => BIO_LIMIT - bio.value.length)

const saving = ref(false)
const error = ref<string | null>(null)

const nameId = useId()
const bioId = useId()
const radiusId = useId()

const firstField = ref<HTMLInputElement | null>(null)
const bioField = ref<HTMLTextAreaElement | null>(null)

/**
 * Поле «О себе» растёт под текст: с прокруткой внутри маленького окошка
 * написанное не видно целиком, а перечитать перед сохранением нужно.
 */
function fitBio(): void {
  const field = bioField.value
  if (!field) return
  field.style.height = 'auto'
  field.style.height = `${field.scrollHeight}px`
}

watch(bio, () => void nextTick(fitBio))

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape' && !saving.value) emit('close')
}

// Фокус в первое поле: иначе с клавиатуры окно открывается «в никуда».
onMounted(() => {
  firstField.value?.focus()
  fitBio()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

/** Картинка уходит в хранилище сразу: в профиль сохраняется уже готовая ссылка. */
async function pickAvatar(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  error.value = null
  try {
    avatarUrl.value = await uploadAvatar(file)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    uploading.value = false
    // Сброс, иначе повторный выбор того же файла не вызовет `change`.
    if (fileInput.value) fileInput.value.value = ''
  }
}

function dropAvatar(): void {
  avatarUrl.value = null
}

async function save(): Promise<void> {
  if (saving.value) return
  saving.value = true
  error.value = null
  try {
    const profile = await updateMyProfile({
      display_name: displayName.value.trim(),
      avatar_url: avatarUrl.value,
      bio: bio.value.trim(),
      subscribed_to_search: subscribed.value,
      alert_radius_km: Number(radius.value) || props.profile.alert_radius_km,
    })
    emit('saved', profile)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-[60] flex items-end justify-center bg-night/60 p-space-sm backdrop-blur-sm"
    role="dialog"
    aria-modal="true"
    aria-label="Редактирование профиля"
    @click.self="saving || emit('close')"
  >
    <!-- `max-h` + прокрутка: с открытой клавиатурой окно иначе не доскроллить до «Сохранить» -->
    <div
      class="flex max-h-[88vh] w-full max-w-app flex-col gap-space-md overflow-y-auto rounded-sheet bg-surface-container-lowest p-space-lg shadow-sheet"
    >
      <div class="flex items-center justify-between">
        <h2 class="font-headline-sm text-headline-sm text-on-surface">Профиль исследователя</h2>
        <button
          type="button"
          aria-label="Закрыть"
          class="flex h-9 w-9 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container"
          :disabled="saving"
          @click="emit('close')"
        >
          <MsIcon name="close" :size="20" />
        </button>
      </div>

      <form class="flex flex-col gap-space-md" @submit.prevent="save">
        <div class="flex items-center gap-space-md">
          <div class="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-surface-container text-on-surface-variant">
            <img v-if="avatarUrl" :src="avatarUrl" alt="" class="h-full w-full object-cover" />
            <MsIcon v-else name="person" :size="36" />
          </div>
          <div class="flex min-w-0 flex-col gap-space-xs">
            <div class="flex flex-wrap gap-space-xs">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 rounded-full bg-surface-container-low px-space-md py-2 font-label-md text-label-md text-on-surface disabled:opacity-60"
                :disabled="uploading || saving"
                @click="fileInput?.click()"
              >
                <MsIcon
                  :name="uploading ? 'progress_activity' : 'photo_camera'"
                  :size="17"
                  :class="{ 'animate-spin': uploading }"
                />
                {{ avatarUrl ? 'Заменить фото' : 'Добавить фото' }}
              </button>
              <button
                v-if="avatarUrl"
                type="button"
                class="inline-flex items-center rounded-full px-space-sm py-2 font-label-md text-label-md text-primary disabled:opacity-60"
                :disabled="uploading || saving"
                @click="dropAvatar"
              >
                Убрать
              </button>
            </div>
            <span class="font-label-sm text-label-sm text-outline">JPEG, PNG или WebP, до 5 МБ</span>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="hidden"
            @change="pickAvatar"
          />
        </div>

        <div class="flex flex-col gap-space-xs">
          <label :for="nameId" class="font-label-md text-label-md text-on-surface-variant">Как вас зовут</label>
          <input
            :id="nameId"
            ref="firstField"
            v-model="displayName"
            type="text"
            maxlength="120"
            placeholder="Имя и фамилия"
            class="rounded-2xl border border-outline-variant bg-surface-container-low px-space-md py-2.5 font-body-md text-body-md text-on-surface outline-none focus:border-primary"
          />
        </div>

        <div class="flex flex-col gap-space-xs">
          <div class="flex items-baseline justify-between gap-space-sm">
            <label :for="bioId" class="font-label-md text-label-md text-on-surface-variant">О себе</label>
            <!-- Счётчик виден заранее: упереться в предел на середине фразы неприятно -->
            <span
              class="font-label-sm text-label-sm tabular-nums"
              :class="bioLeft <= 20 ? 'text-primary' : 'text-outline'"
            >
              {{ bio.length }} / {{ BIO_LIMIT }}
            </span>
          </div>
          <textarea
            :id="bioId"
            ref="bioField"
            v-model="bio"
            rows="2"
            :maxlength="BIO_LIMIT"
            placeholder="Чем занимаетесь в поиске, какой отряд, что ищете"
            class="resize-none overflow-hidden rounded-2xl border border-outline-variant bg-surface-container-low px-space-md py-2.5 font-body-md text-body-md text-on-surface outline-none focus:border-primary"
          />
        </div>

        <div class="flex items-center justify-between gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
          <div class="flex min-w-0 flex-col">
            <span class="font-label-md text-label-md text-on-surface">Оповещения о находках рядом</span>
            <span class="font-label-sm text-label-sm text-on-surface-variant">Сообщать, когда поиск идёт поблизости</span>
          </div>
          <ToggleSwitch v-model="subscribed" label="Оповещения о находках рядом" />
        </div>

        <!-- Радиус нужен только подписанным: без подписки поле ни на что не влияет -->
        <div v-if="subscribed" class="flex items-center justify-between gap-space-sm">
          <label :for="radiusId" class="font-label-md text-label-md text-on-surface-variant">Радиус, км</label>
          <input
            :id="radiusId"
            v-model.number="radius"
            type="number"
            min="1"
            max="500"
            class="w-24 rounded-2xl border border-outline-variant bg-surface-container-low px-space-sm py-2 text-center font-body-md text-body-md tabular-nums text-on-surface outline-none focus:border-primary"
          />
        </div>

        <p v-if="error" class="rounded-2xl bg-error-container px-space-sm py-2 font-body-sm text-body-sm text-on-error-container" role="alert">
          {{ error }}
        </p>

        <button
          type="submit"
          class="flex items-center justify-center gap-space-xs rounded-full bg-primary py-3 font-label-lg text-label-lg text-on-primary shadow-sm disabled:opacity-70"
          :disabled="saving"
        >
          <MsIcon :name="saving ? 'progress_activity' : 'save'" :size="18" :class="{ 'animate-spin': saving }" />
          Сохранить
        </button>
      </form>
    </div>
  </div>
</template>
