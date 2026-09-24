<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { errorText } from '@/core/format'
import { usePreferencesStore } from '@/core/preferences'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'
import FormSelect from '@/ui/form/FormSelect.vue'

import { updateProfile, type Profile, type ProfilePatch, type SquadOption } from '../data'

/**
 * Настройки: гео-оповещения о новых местах «Последнего боя» и радиус (кейс:
 * «в радиусе 20 км приходит пуш»), отряд, в котором человек состоит, и
 * семейный режим. Первые три хранит `user_service`, семейный режим — телефон.
 */
const props = defineProps<{
  /** `null` — демо-режим: серверных настроек нет, остаётся только семейный режим. */
  profile: Profile | null
  squads: SquadOption[]
}>()

const emit = defineEmits<{ saved: [profile: Profile] }>()

/** Ползунок радиуса шлёт запрос не на каждый пиксель, а когда палец остановился. */
const RADIUS_DEBOUNCE_MS = 600

const router = useRouter()
const preferences = usePreferencesStore()
const subscribed = ref(false)
const radius = ref(20)
const squadId = ref('')
const error = ref<string | null>(null)
const saving = ref(false)
let radiusTimer: ReturnType<typeof setTimeout> | undefined

watch(
  () => props.profile,
  (profile) => {
    subscribed.value = profile?.subscribed_to_search ?? false
    radius.value = profile?.alert_radius_km ?? 20
    squadId.value = profile?.squad_id ?? ''
  },
  { immediate: true },
)

/** Без своей точки сервис не знает, от чего считать «рядом», — задают её на карте «Последнего боя». */
const hasHome = computed(() => props.profile?.home_lat != null && props.profile?.home_lon != null)
const canOpenLastStand = computed(() => router.hasRoute('last-stand'))

const squadOptions = computed(() => [{ value: 'none', title: 'Не состою в отряде' }, ...props.squads.map((squad) => ({ value: squad.id, title: squad.name }))])
const squadChoice = computed({
  get: () => squadId.value || 'none',
  set: (value: string) => {
    squadId.value = value === 'none' ? '' : value
    void save({ squad_id: squadId.value })
  },
})

async function save(patch: ProfilePatch): Promise<void> {
  if (!props.profile) return
  saving.value = true
  error.value = null
  try {
    emit('saved', await updateProfile(patch))
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

function toggleAlerts(value: boolean): void {
  subscribed.value = value
  void save({ subscribed_to_search: value })
}

function onRadius(value: number): void {
  radius.value = value
  clearTimeout(radiusTimer)
  radiusTimer = setTimeout(() => void save({ alert_radius_km: value }), RADIUS_DEBOUNCE_MS)
}

onBeforeUnmount(() => clearTimeout(radiusTimer))
</script>

<template>
  <section class="flex flex-col gap-space-sm">
    <div class="flex items-end justify-between gap-space-sm">
      <div>
        <p class="font-archival text-archival uppercase text-on-surface-variant">Настройки</p>
        <h2 class="font-headline-md text-headline-md text-on-surface">Оповещения и режимы</h2>
      </div>
      <MsIcon v-if="saving" name="progress_activity" :size="20" class="mb-1 animate-spin text-on-surface-variant" />
    </div>

    <div class="flex flex-col rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
      <template v-if="profile">
        <div class="flex items-center justify-between gap-space-sm">
          <div class="flex min-w-0 items-center gap-space-sm">
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container" aria-hidden="true">
              <MsIcon name="radar" :size="18" />
            </span>
            <div class="min-w-0">
              <p class="font-label-lg text-label-lg text-on-surface">Находки рядом</p>
              <p class="font-body-sm text-body-sm text-on-surface-variant">Новые места «Последнего боя» в радиусе {{ radius }} км</p>
            </div>
          </div>
          <ToggleSwitch :model-value="subscribed" label="Оповещения о находках рядом" @update:model-value="toggleAlerts" />
        </div>

        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="subscribed ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          :inert="!subscribed"
        >
          <div class="flex flex-col gap-space-sm overflow-hidden pl-12">
            <label class="flex flex-col gap-1 pt-space-sm">
              <span class="sr-only">Радиус оповещений, км</span>
              <input
                type="range"
                min="1"
                max="200"
                step="1"
                :value="radius"
                class="w-full accent-secondary"
                @input="onRadius(Number(($event.target as HTMLInputElement).value))"
              />
              <span class="flex justify-between font-label-sm text-label-sm text-on-surface-variant"><span>1 км</span><span>200 км</span></span>
            </label>
            <p class="flex items-start gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
              <MsIcon :name="hasHome ? 'home_pin' : 'info'" :size="18" class="shrink-0" :class="hasHome ? 'text-secondary' : ''" />
              <span>
                {{ hasHome ? 'Считаем от вашей точки на карте.' : 'Своя точка не задана — без неё сервис не знает, что для вас «рядом».' }}
                <RouterLink
                  v-if="canOpenLastStand"
                  :to="{ name: 'last-stand' }"
                  class="font-label-md text-label-md text-secondary underline-offset-2 hover:underline"
                >
                  {{ hasHome ? 'Изменить' : 'Задать на карте' }}
                </RouterLink>
              </span>
            </p>
          </div>
        </div>

        <div class="my-space-md h-px bg-outline-variant/60" />

        <FormSelect v-model="squadChoice" label="Мой поисковый отряд" :options="squadOptions" />

        <div class="my-space-md h-px bg-outline-variant/60" />
      </template>

      <div class="flex items-center justify-between gap-space-sm">
        <div class="flex min-w-0 items-center gap-space-sm">
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-on-tertiary-fixed" aria-hidden="true">
            <MsIcon name="family_restroom" :size="18" />
          </span>
          <div class="min-w-0">
            <p class="font-label-lg text-label-lg text-on-surface">Семейный и детский режим</p>
            <p class="font-body-sm text-body-sm text-on-surface-variant">Детские задания на маршрутах, мягкая подача</p>
          </div>
        </div>
        <ToggleSwitch v-model="preferences.familyMode" label="Семейный и детский режим" />
      </div>
    </div>

    <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
  </section>
</template>
