<script setup>
import { computed, onMounted, ref } from 'vue'
import LeafletMap from '@shared/components/LeafletMap.vue'
import DirectionsButton from '@shared/components/DirectionsButton.vue'
import PointReviews from '@shared/components/PointReviews.vue'
import { useAuthSession } from '@modules/auth'
import * as routesApi from '../api.js'

const FALLBACK_CENTER = [52.9651, 36.0785] // Орёл

// EntryService.VERIFIER_ROLES (archive_service) — кто может подтвердить/отклонить
// запись народного архива.
const VERIFIER_ROLES = new Set(['searcher', 'local_historian', 'mentor', 'moderator'])

const ENTRY_KIND_LABELS = {
  event: 'Локальное событие',
  memory: 'Воспоминание очевидца',
  soldier_card: 'Карточка бойца',
  photo_story: 'Фото + история',
}

const KIND_META = {
  grave: { label: 'Захоронения', icon: 'flag', dot: 'bg-error', badgeClass: 'bg-error', tailClass: 'border-t-error' },
  monument: {
    label: 'Памятники',
    icon: 'account_balance',
    dot: 'bg-secondary',
    badgeClass: 'bg-secondary',
    tailClass: 'border-t-secondary',
  },
  battle: { label: 'Места боёв', icon: 'star', dot: 'bg-tertiary', badgeClass: 'bg-tertiary', tailClass: 'border-t-tertiary' },
  hospital: {
    label: 'Госпитали',
    icon: 'medical_services',
    dot: 'bg-primary',
    badgeClass: 'bg-primary',
    tailClass: 'border-t-primary',
  },
  trench: { label: 'Окопы', icon: 'sports_motorsports', dot: 'bg-outline', badgeClass: 'bg-outline', tailClass: 'border-t-outline' },
  airfield: { label: 'Аэродромы', icon: 'flight', dot: 'bg-outline', badgeClass: 'bg-outline', tailClass: 'border-t-outline' },
  other: { label: 'Другое', icon: 'push_pin', dot: 'bg-outline', badgeClass: 'bg-outline', tailClass: 'border-t-outline' },
}

// По умолчанию — то, к чему семья реально может сходить пешком или доехать:
// захоронения и памятники. Остальные слои включаются вручную.
const activeKinds = ref(new Set(['grave', 'monument']))
const points = ref([])
const status = ref('loading') // loading | ready | error
const selectedId = ref(null)

const { session } = useAuthSession()
const pendingEntries = ref([])
const selectedPendingId = ref(null)
const reviewStatus = ref('idle') // idle | pending
const reviewError = ref('')

const canVerify = computed(
  () => session.status === 'authenticated' && (session.user?.is_root || VERIFIER_ROLES.has(session.user?.role)),
)

async function loadNearbyPending(pts) {
  // Бокс вокруг всех видимых точек слоя «ВОВ» (плюс отступ), а не всей карты —
  // иначе на масштабе региона подсказка почти всегда будет пустой или наоборот
  // покажет вообще всё. Нет точек — не показываем подсказку вовсе.
  if (!pts.length) return
  const lats = pts.map((p) => p.lat)
  const lons = pts.map((p) => p.lon)
  const pad = 0.15
  try {
    pendingEntries.value = await routesApi.listNearbyPendingEntries({
      minLat: Math.min(...lats) - pad,
      minLon: Math.min(...lons) - pad,
      maxLat: Math.max(...lats) + pad,
      maxLon: Math.max(...lons) + pad,
    })
  } catch {
    // best-effort подсказка — молча ничего не показываем при сбое
  }
}

onMounted(async () => {
  try {
    points.value = await routesApi.listPoi()
    status.value = 'ready'
    loadNearbyPending(points.value)
  } catch {
    status.value = 'error'
  }
})

function toggleKind(kind) {
  const next = new Set(activeKinds.value)
  if (next.has(kind)) next.delete(kind)
  else next.add(kind)
  activeKinds.value = next
  selectedId.value = null
}

const visiblePoints = computed(() => points.value.filter((p) => activeKinds.value.has(p.kind)))

const visiblePendingEntries = computed(() => pendingEntries.value.filter((e) => e.lat != null && e.lon != null))

const markers = computed(() => [
  ...visiblePoints.value.map((p) => ({
    id: p.id,
    lat: p.lat,
    lng: p.lon,
    title: p.title,
    subtitle: KIND_META[p.kind]?.label,
    icon: KIND_META[p.kind]?.icon ?? 'push_pin',
    badgeClass: KIND_META[p.kind]?.badgeClass,
    tailClass: KIND_META[p.kind]?.tailClass,
  })),
  ...visiblePendingEntries.value.map((e) => ({
    id: `pending:${e.id}`,
    lat: e.lat,
    lng: e.lon,
    title: e.title,
    subtitle: 'Народный архив: требует проверки',
    icon: 'fact_check',
    badgeClass: 'bg-tertiary',
    tailClass: 'border-t-tertiary',
  })),
])

function onMarkerClick(id) {
  if (typeof id === 'string' && id.startsWith('pending:')) {
    selectedPendingId.value = id.slice('pending:'.length)
    selectedId.value = null
  } else {
    selectedId.value = id
    selectedPendingId.value = null
  }
  reviewError.value = ''
}

const mapRef = ref(null)

const selected = computed(() => points.value.find((p) => p.id === selectedId.value) ?? null)
const selectedPending = computed(() => pendingEntries.value.find((e) => e.id === selectedPendingId.value) ?? null)

async function reviewEntry(action) {
  if (!selectedPending.value) return
  reviewStatus.value = 'pending'
  reviewError.value = ''
  try {
    const call = action === 'verify' ? routesApi.verifyArchiveEntry : routesApi.rejectArchiveEntry
    await call(session.accessToken, selectedPending.value.id)
    pendingEntries.value = pendingEntries.value.filter((e) => e.id !== selectedPending.value.id)
    selectedPendingId.value = null
  } catch (err) {
    reviewError.value = err.detail ?? 'Не удалось отправить решение'
  } finally {
    reviewStatus.value = 'idle'
  }
}

const kindsPresent = computed(() => {
  const present = new Set(points.value.map((p) => p.kind))
  return Object.keys(KIND_META).filter((k) => present.has(k))
})

function formatAdded(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>

<template>
  <section class="bg-surface-container-lowest rounded-lg shadow-sm overflow-hidden">
    <div class="p-5 pb-4 flex flex-col gap-3">
      <div class="flex items-start justify-between gap-3 flex-wrap">
        <div class="flex flex-col">
          <h2 class="font-headline-sm text-headline-sm text-on-surface">Куда можно сходить</h2>
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            Слой «ВОВ»: захоронения и памятники рядом — данные из map_service
          </p>
        </div>
        <span v-if="status === 'ready'" class="font-label-sm text-label-sm text-on-surface-variant">
          {{ visiblePoints.length }} точек на карте
        </span>
      </div>

      <p
        v-if="visiblePendingEntries.length"
        class="flex items-center gap-2 px-3.5 py-2.5 rounded-DEFAULT bg-tertiary-fixed text-on-tertiary-fixed font-body-sm text-body-sm"
      >
        <span class="material-symbols-outlined text-[18px] shrink-0">fact_check</span>
        <span>
          Рядом {{ visiblePendingEntries.length }}
          {{ visiblePendingEntries.length === 1 ? 'неподтверждённая запись' : 'неподтверждённых записи' }}
          «Живой памяти» — помогите проверить (отмечены на карте).
        </span>
      </p>

      <div v-if="kindsPresent.length" class="flex flex-wrap gap-2">
        <button
          v-for="kind in kindsPresent"
          :key="kind"
          type="button"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-full font-label-sm text-label-sm font-bold transition-all"
          :class="
            activeKinds.has(kind)
              ? 'bg-secondary text-on-secondary'
              : 'bg-surface-container-low text-on-surface-variant hover:bg-surface-container'
          "
          @click="toggleKind(kind)"
        >
          <span class="material-symbols-outlined text-[16px]">{{ KIND_META[kind].icon }}</span>
          {{ KIND_META[kind].label }}
        </button>
      </div>
    </div>

    <div class="relative h-96">
      <div v-if="status === 'loading'" class="absolute inset-0 flex items-center justify-center bg-surface-container">
        <span class="font-label-md text-label-md text-on-surface-variant flex items-center gap-2">
          <span class="material-symbols-outlined animate-spin text-[18px]">sync</span>
          Загружаем точки карты...
        </span>
      </div>
      <div v-else-if="status === 'error'" class="absolute inset-0 flex items-center justify-center bg-surface-container p-4 text-center">
        <span class="font-label-md text-label-md text-on-surface-variant">
          Не удалось загрузить слой «ВОВ» — map_service недоступен
        </span>
      </div>
      <template v-else>
        <LeafletMap ref="mapRef" :center="FALLBACK_CENTER" :zoom="9" :markers="markers" @marker-click="onMarkerClick" />
        <p v-if="!visiblePoints.length" class="absolute inset-x-0 top-3 flex justify-center pointer-events-none">
          <span class="px-3 py-1.5 rounded-full bg-surface-container-lowest/90 backdrop-blur font-label-sm text-label-sm text-on-surface-variant">
            Включите хотя бы один слой выше
          </span>
        </p>
        <div class="absolute top-3 right-3 flex flex-col gap-1.5 z-10">
          <button
            type="button"
            class="w-9 h-9 rounded-full bg-surface-container-lowest/95 backdrop-blur shadow-md hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors"
            title="Приблизить"
            @click="mapRef?.zoomIn()"
          >
            <span class="material-symbols-outlined text-[20px]">add</span>
          </button>
          <button
            type="button"
            class="w-9 h-9 rounded-full bg-surface-container-lowest/95 backdrop-blur shadow-md hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors"
            title="Отдалить"
            @click="mapRef?.zoomOut()"
          >
            <span class="material-symbols-outlined text-[20px]">remove</span>
          </button>
        </div>
      </template>
    </div>

    <div v-if="selected" class="p-5 border-t border-surface-container-high flex flex-col gap-4">
      <div class="flex items-start gap-3">
        <div class="w-9 h-9 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-[18px]">{{ KIND_META[selected.kind]?.icon ?? 'push_pin' }}</span>
        </div>
        <div class="flex flex-col gap-1 min-w-0">
          <span class="font-label-lg text-label-lg text-on-surface font-bold">{{ selected.title }}</span>
          <span v-if="selected.description" class="font-body-sm text-body-sm text-on-surface-variant">{{ selected.description }}</span>
          <span v-if="selected.date_text" class="font-label-sm text-label-sm text-secondary font-bold">{{ selected.date_text }}</span>
          <span v-if="selected.source" class="font-label-sm text-label-sm text-on-surface-variant">Источник: {{ selected.source }}</span>
          <span class="font-label-sm text-label-sm text-on-surface-variant">Добавлено в map_service: {{ formatAdded(selected.created_at) }}</span>
        </div>
      </div>

      <DirectionsButton :point="selected" />
      <PointReviews :point="selected" />
    </div>

    <div v-if="selectedPending" class="p-5 border-t border-surface-container-high flex flex-col gap-3">
      <div class="flex items-start gap-3">
        <div class="w-9 h-9 rounded-full bg-tertiary-container text-on-tertiary-container flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-[18px]">fact_check</span>
        </div>
        <div class="flex flex-col gap-1 min-w-0">
          <span class="font-label-lg text-label-lg text-on-surface font-bold">{{ selectedPending.title }}</span>
          <span class="font-label-sm text-label-sm text-tertiary font-bold">
            {{ ENTRY_KIND_LABELS[selectedPending.kind] ?? selectedPending.kind }} · народный архив, ждёт проверки
          </span>
          <span class="font-label-sm text-label-sm text-on-surface-variant">
            Предложено: {{ new Date(selectedPending.created_at).toLocaleDateString('ru-RU') }}
          </span>
        </div>
      </div>

      <p v-if="reviewError" class="font-label-sm text-label-sm text-error font-bold">{{ reviewError }}</p>

      <div v-if="canVerify" class="flex gap-2">
        <button
          type="button"
          class="flex-1 h-11 rounded-full bg-secondary text-on-secondary font-label-md text-label-md font-bold flex items-center justify-center gap-2 disabled:opacity-60"
          :disabled="reviewStatus === 'pending'"
          @click="reviewEntry('verify')"
        >
          <span class="material-symbols-outlined text-[18px]">check_circle</span>
          Подтвердить
        </button>
        <button
          type="button"
          class="flex-1 h-11 rounded-full bg-error-container text-on-error-container font-label-md text-label-md font-bold flex items-center justify-center gap-2 disabled:opacity-60"
          :disabled="reviewStatus === 'pending'"
          @click="reviewEntry('reject')"
        >
          <span class="material-symbols-outlined text-[18px]">cancel</span>
          Отклонить
        </button>
      </div>
      <p v-else-if="session.status === 'authenticated'" class="font-body-sm text-body-sm text-on-surface-variant">
        Проверять записи народного архива могут поисковики, краеведы, наставники и модераторы.
        <RouterLink to="/profile" class="text-primary font-bold hover:underline">Подайте заявку на статус краеведа</RouterLink>,
        чтобы участвовать в проверке.
      </p>
      <p v-else class="font-body-sm text-body-sm text-on-surface-variant">
        <RouterLink to="/auth" class="text-primary font-bold hover:underline">Войдите</RouterLink>,
        чтобы помочь проверить эту запись.
      </p>
    </div>
  </section>
</template>
