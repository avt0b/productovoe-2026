<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

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
  <section class="mt-2 flex flex-col gap-space-sm">
    <div class="flex items-center justify-between px-1">
      <div>
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Настройки и экспедиции</h3>
        <span class="font-body-sm text-body-sm text-on-surface-variant">Оповещения, отряд и семейный режим</span>
      </div>
      <MsIcon v-if="saving" name="progress_activity" :size="20" class="animate-spin text-outline" />
    </div>

    <div class="flex flex-col rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
      <template v-if="profile">
        <div class="flex items-center justify-between gap-space-sm">
          <div class="flex min-w-0 items-center gap-space-sm">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-secondary-fixed text-secondary">
              <MsIcon name="radar" :size="20" />
            </div>
            <div class="min-w-0">
              <h4 class="font-label-lg text-label-lg font-bold text-on-surface">Оповещения о находках рядом</h4>
              <p class="font-body-sm text-body-sm text-on-surface-variant">
                Новые места «Последнего боя» в радиусе {{ radius }} км
              </p>
            </div>
          </div>
          <ToggleSwitch :model-value="subscribed" label="Оповещения о находках рядом" @update:model-value="toggleAlerts" />
        </div>

        <label v-if="subscribed" class="mt-space-sm flex flex-col gap-1 pl-12">
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
          <span class="flex justify-between font-label-sm text-label-sm text-outline"><span>1 км</span><span>200 км</span></span>
        </label>

        <div class="my-space-md h-px bg-surface-container" />

        <FormSelect v-model="squadChoice" label="Мой поисковый отряд" :options="squadOptions" />

        <div class="my-space-md h-px bg-surface-container" />
      </template>

      <div class="flex items-center justify-between gap-space-sm">
        <div class="flex min-w-0 items-center gap-space-sm">
          <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-tertiary">
            <MsIcon name="family_restroom" :size="20" />
          </div>
          <div class="min-w-0">
            <h4 class="font-label-lg text-label-lg font-bold text-on-surface">Семейный и детский режим</h4>
            <p class="font-body-sm text-body-sm text-on-surface-variant">Детские задания на маршрутах, мягкая подача</p>
          </div>
        </div>
        <ToggleSwitch v-model="preferences.familyMode" label="Семейный и детский режим" />
      </div>
    </div>

    <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
  </section>
</template>
