<script setup lang="ts">
import { ref } from 'vue'

import { usePreferencesStore } from '@/core/preferences'
import MsIcon from '@/ui/MsIcon.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'

import type { AppSetting } from '../data'

const props = defineProps<{ settings: AppSetting[] }>()

/**
 * Семейный режим — общий флаг ядра: его же включают на экране входа.
 * Остальные переключатели пока живут в экране; сохранять их будет `user_service`.
 */
const preferences = usePreferencesStore()
const local = ref(props.settings.map((setting) => ({ ...setting })))

const TONES: Record<AppSetting['tone'], string> = {
  secondary: 'bg-secondary-fixed text-secondary',
  neutral: 'bg-surface-container text-on-surface-variant',
}
</script>

<template>
  <section class="mt-2 flex flex-col gap-space-sm">
    <div class="px-1">
      <h3 class="font-headline-sm text-headline-sm text-on-surface">Настройки приложения и экспедиций</h3>
      <span class="font-body-sm text-body-sm text-on-surface-variant">Параметры работы на местности и в семье</span>
    </div>

    <div class="flex flex-col rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
      <template v-for="(setting, index) in local" :key="setting.id">
        <div v-if="index > 0" class="my-space-md h-px bg-surface-container" />
        <div class="flex items-center justify-between gap-space-sm">
          <div class="flex min-w-0 items-center gap-space-sm">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full" :class="TONES[setting.tone]">
              <MsIcon :name="setting.icon" :size="20" />
            </div>
            <div class="min-w-0">
              <h4 class="font-label-lg text-label-lg font-bold text-on-surface">{{ setting.title }}</h4>
              <p class="font-body-sm text-body-sm text-on-surface-variant">{{ setting.description }}</p>
            </div>
          </div>
          <ToggleSwitch v-model="setting.enabled" :label="setting.title" />
        </div>

        <!-- Семейный режим встаёт третьим, как в макете. -->
        <template v-if="index === 1">
          <div class="my-space-md h-px bg-surface-container" />
          <div class="flex items-center justify-between gap-space-sm">
            <div class="flex min-w-0 items-center gap-space-sm">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-tertiary">
                <MsIcon name="family_restroom" :size="20" />
              </div>
              <div class="min-w-0">
                <h4 class="font-label-lg text-label-lg font-bold text-on-surface">Семейный и детский режим</h4>
                <p class="font-body-sm text-body-sm text-on-surface-variant">Фильтр тяжелых архивных деталей, мягкая подача</p>
              </div>
            </div>
            <ToggleSwitch v-model="preferences.familyMode" label="Семейный и детский режим" />
          </div>
        </template>
      </template>
    </div>
  </section>
</template>
