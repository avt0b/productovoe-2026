<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import { ApiError } from '@/core/api'
import { errorText } from '@/core/format'
import {
  ROUTE_FILE_MAX_MB,
  createRoute,
  updateRoute,
  uploadRouteFile,
  type RouteMode,
  type RouteSummary,
} from '@/core/services/routes'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

/**
 * Маршрут краеведа: заголовок и описание. Новый маршрут заводится черновиком —
 * опубликовать его можно, только когда в нём есть точки (так решает сервис).
 */
const props = defineProps<{
  /** `null` — заводим новый маршрут. */
  route: RouteSummary | null
}>()

const emit = defineEmits<{ close: []; saved: [route: RouteSummary] }>()

const MODES: readonly { value: RouteMode; title: string }[] = [
  { value: 'family', title: 'Семейный: с заданиями для детей' },
  { value: 'general', title: 'Общий: для всех' },
]

const title = ref(props.route?.title ?? '')
const description = ref(props.route?.description ?? '')
const city = ref(props.route?.city ?? 'Орёл')
const mode = ref<RouteMode>(props.route?.mode ?? 'family')
const distance = ref<number | null>(props.route?.distance_km ?? null)
const coverUrl = ref<string | null>(props.route?.cover_url ?? null)
const coverInput = ref<HTMLInputElement | null>(null)
/** Снимок с телефона, пока он грузится: ждать адреса, глядя на пустой прямоугольник, незачем. */
const localCover = ref<string | null>(null)
const uploading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const cover = computed(() => localCover.value ?? coverUrl.value)

function dropLocalCover(): void {
  if (localCover.value) URL.revokeObjectURL(localCover.value)
  localCover.value = null
}

async function pickCover(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  dropLocalCover()
  localCover.value = URL.createObjectURL(file)
  error.value = null
  uploading.value = true
  try {
    coverUrl.value = await uploadRouteFile(file)
  } catch (reason) {
    dropLocalCover()
    // 503 — хранилище не поднято: маршрут это не отменяет, обложку добавят позже.
    error.value =
      reason instanceof ApiError && reason.status === 503
        ? 'Хранилище фото сейчас недоступно. Сохраните маршрут без обложки — добавите позже.'
        : errorText(reason)
  } finally {
    uploading.value = false
  }
}

function removeCover(): void {
  dropLocalCover()
  coverUrl.value = null
  error.value = null
}

onBeforeUnmount(dropLocalCover)

const missing = computed(() => (title.value.trim() ? null : 'Назовите маршрут'))

async function save(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  const draft = {
    title: title.value.trim(),
    description: description.value.trim(),
    city: city.value.trim(),
    mode: mode.value,
    distance_km: Math.max(0, distance.value ?? 0),
    cover_url: coverUrl.value,
  }
  try {
    emit('saved', props.route ? await updateRoute(props.route.id, draft) : await createRoute(draft))
    emit('close')
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog
    :title="route ? 'Изменить маршрут' : 'Новый маршрут'"
    subtitle="Черновик видите только вы — пока не опубликуете"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-md" @submit.prevent="save">
      <FormInput v-model="title" label="Название" icon="route" :maxlength="255" placeholder="Тропа памяти: центр Орла" required />
      <FormTextarea
        v-model="description"
        label="О чём маршрут"
        :rows="3"
        placeholder="Что увидят на маршруте и почему это место важно"
      />
      <FormSelect v-model="mode" label="Для кого" :options="MODES" icon="family_restroom" />
      <FormInput v-model="city" label="Город или район" icon="home_pin" :maxlength="120" placeholder="Орёл" />
      <FormInput
        v-model="distance"
        label="Длина, км"
        icon="directions_walk"
        type="number"
        :min="0"
        :max="100"
        :step="0.1"
        inputmode="decimal"
        hint="Примерная — её видно в карточке маршрута"
      />

      <div class="flex items-center gap-space-md">
        <span
          class="relative flex h-20 w-28 shrink-0 items-center justify-center overflow-hidden rounded-DEFAULT border border-dashed border-outline-variant bg-surface-container-low text-on-surface-variant"
        >
          <img v-if="cover" :src="cover" alt="" class="h-full w-full object-cover" :class="{ 'opacity-50': uploading }" />
          <MsIcon v-else name="image" :size="24" />
          <MsIcon v-if="uploading" name="progress_activity" :size="20" class="absolute animate-spin" />
        </span>
        <div class="flex min-w-0 flex-col items-start gap-space-xs">
          <button
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95 disabled:opacity-60"
            :disabled="uploading"
            @click="coverInput?.click()"
          >
            <MsIcon name="add_a_photo" :size="18" />
            {{ cover ? 'Заменить обложку' : 'Обложка маршрута' }}
          </button>
          <button
            v-if="cover"
            type="button"
            class="px-space-xs font-label-md text-label-md text-on-surface-variant active:scale-95"
            @click="removeCover"
          >
            Убрать обложку
          </button>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Необязательно, JPEG, PNG или WebP, до {{ ROUTE_FILE_MAX_MB }} МБ
          </p>
        </div>
      </div>
      <input ref="coverInput" type="file" accept="image/jpeg,image/png,image/webp" class="sr-only" tabindex="-1" @change="pickCover" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving || uploading"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'save'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ route ? 'Сохранить' : 'Создать черновик' }}</span>
      </button>
    </form>
  </SheetDialog>
</template>
