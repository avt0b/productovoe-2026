<script setup>
import { reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import ToggleSwitch from '@shared/components/ToggleSwitch.vue'
import MobileOnlyBadge from '@shared/components/MobileOnlyBadge.vue'
import { useAuthSession } from '@modules/auth'
import { useProfileStore } from '../profileStore.js'

const router = useRouter()
const { session, logout } = useAuthSession()
const { profile, saveMyProfile } = useProfileStore()

const toggles = reactive({
  geoAlerts: false,
  familyMode: true,
  audioGuides: true,
})
const alertRadiusKm = reactive({ value: 15 })

watch(
  () => profile.data,
  (data) => {
    if (!data) return
    toggles.geoAlerts = data.subscribed_to_search
    alertRadiusKm.value = data.alert_radius_km
  },
  { immediate: true },
)

async function onGeoAlertsChange(value) {
  toggles.geoAlerts = value
  if (session.status !== 'authenticated') return
  try {
    await saveMyProfile({ subscribed_to_search: value })
  } catch {
    toggles.geoAlerts = !value // откатываем переключатель, если сохранение не удалось
  }
}

async function signOut() {
  await logout()
  router.push('/auth')
}
</script>

<template>
  <div class="bg-surface-container-lowest p-6 rounded-DEFAULT shadow-sm flex flex-col">
    <div class="flex items-center gap-3 mb-6">
      <div class="w-10 h-10 rounded-full bg-surface-container-high text-on-surface flex items-center justify-center">
        <span class="material-symbols-outlined text-[20px]">tune</span>
      </div>
      <div class="flex flex-col">
        <h2 class="font-headline-sm text-headline-sm font-bold text-on-surface">Настройки экспедиций</h2>
        <span class="font-body-sm text-body-sm text-on-surface-variant">Оффлайн-режим и полевые триггеры</span>
      </div>
    </div>

    <div class="flex flex-col gap-5">
      <div class="bg-surface-container-low p-4 rounded-DEFAULT flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-secondary text-[24px]">download_done</span>
            <div class="flex flex-col">
              <span class="font-label-md text-label-md font-bold text-on-surface flex items-center gap-1.5 flex-wrap">
                Оффлайн-карты рубежей
                <span class="px-1.5 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant text-[10px] font-bold uppercase">
                  демо
                </span>
              </span>
              <span class="font-body-sm text-body-sm text-on-surface-variant">Ни в одном сервисе нет офлайн-карт</span>
            </div>
          </div>
          <span class="font-label-sm text-label-sm bg-secondary-fixed text-on-secondary-fixed font-bold px-2.5 py-1 rounded-full">
            1.2 ГБ
          </span>
        </div>
        <div class="w-full bg-surface-container-high h-2 rounded-full overflow-hidden">
          <div class="bg-secondary h-full rounded-full" style="width: 100%" />
        </div>
        <div class="flex items-center justify-between text-on-surface-variant font-label-sm text-label-sm">
          <span>Синхронизировано вчера в 18:40</span>
          <button class="text-primary font-bold hover:underline">Обновить сектор</button>
        </div>
      </div>

      <div class="flex items-center justify-between gap-4">
        <div class="flex items-start gap-3">
          <span class="material-symbols-outlined text-on-surface-variant text-[22px] mt-0.5">location_on</span>
          <div class="flex flex-col">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-label-md text-label-md font-bold text-on-surface">Гео-оповещения раскопок</span>
              <MobileOnlyBadge label="Push — в приложении" />
            </div>
            <span class="font-body-sm text-body-sm text-on-surface-variant">
              Подписка на «поисковую деятельность» (user_service), радиус {{ alertRadiusKm.value }} км —
              сама доставка push пока доступна только в приложении
            </span>
          </div>
        </div>
        <ToggleSwitch :model-value="toggles.geoAlerts" @update:model-value="onGeoAlertsChange" />
      </div>

      <div class="flex items-center justify-between gap-4">
        <div class="flex items-start gap-3">
          <span class="material-symbols-outlined text-on-surface-variant text-[22px] mt-0.5">family_restroom</span>
          <div class="flex flex-col">
            <span class="font-label-md text-label-md font-bold text-on-surface">Семейный и детский режим</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">
              Упрощённые описания, игровые квесты для детей
            </span>
          </div>
        </div>
        <ToggleSwitch v-model="toggles.familyMode" />
      </div>

      <div class="flex items-center justify-between gap-4">
        <div class="flex items-start gap-3">
          <span class="material-symbols-outlined text-on-surface-variant text-[22px] mt-0.5">headphones</span>
          <div class="flex flex-col">
            <span class="font-label-md text-label-md font-bold text-on-surface">Автозапуск аудиогидов</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">
              Включать историческую справку при входе в контрольную точку
            </span>
          </div>
        </div>
        <ToggleSwitch v-model="toggles.audioGuides" />
      </div>
    </div>

    <div class="mt-8 pt-6 flex flex-col sm:flex-row items-center gap-3">
      <button
        class="w-full sm:flex-1 bg-surface-container hover:bg-surface-container-high text-on-surface font-label-md text-label-md font-bold py-3 px-4 rounded-full transition-colors flex items-center justify-center gap-2"
      >
        <span class="material-symbols-outlined text-[18px]">sync</span>
        <span>Синхронизировать заметки</span>
      </button>
      <button
        class="w-full sm:w-auto bg-error-container hover:bg-error/20 text-on-error-container font-label-md text-label-md font-bold py-3 px-5 rounded-full transition-colors flex items-center justify-center gap-1.5"
        @click="signOut"
      >
        <span class="material-symbols-outlined text-[18px]">logout</span>
        <span>Выйти</span>
      </button>
    </div>
  </div>
</template>
