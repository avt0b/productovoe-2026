<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { Profile } from '../api'
import { memberSince, roleTitle } from '../data'

const props = defineProps<{
  profile: Profile
  /** Почта из `auth_service`: в профиле `user_service` её нет. */
  email?: string
}>()

defineEmits<{ edit: [] }>()

const since = computed(() => memberSince(props.profile.created_at))

/**
 * У нового профиля `display_name` пустой — бэкенд не подставляет туда ничего
 * при регистрации. Показываем почту до первой правки профиля, иначе в шапке
 * карточки зияет пустая строка.
 */
const name = computed(() => props.profile.display_name || props.email?.split('@')[0] || 'Исследователь')
</script>

<template>
  <!--
    Карточка показывает ровно то, что отдаёт `user_service`: имя, роль, город,
    описание, отряд, признак проверенного профиля и дату регистрации. Почта
    приходит из сессии — в профиле её нет.
  -->
  <article
    class="relative flex flex-col gap-space-md overflow-hidden bg-secondary p-space-lg text-on-secondary shadow-lg"
  >
    <div class="pointer-events-none absolute -bottom-10 -right-8 h-44 w-44 rounded-full bg-secondary-container/10 blur-xl" />
    <div class="pointer-events-none absolute -left-6 -top-6 h-32 w-32 rounded-full bg-surface-container-lowest/5" />

    <div class="relative z-10 flex items-start gap-space-md">
      <div class="relative shrink-0">
        <div
          class="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-secondary-fixed text-secondary shadow-md"
        >
          <img v-if="profile.avatar_url" :src="profile.avatar_url" alt="" class="h-full w-full object-cover" />
          <MsIcon v-else name="person" :size="32" />
        </div>
        <!-- Галочка только у проверенного профиля: это поле `is_verified`, а не украшение -->
        <div
          v-if="profile.is_verified"
          class="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary shadow-sm"
          title="Профиль подтверждён"
        >
          <MsIcon name="verified" :size="15" filled />
        </div>
      </div>

      <div class="flex min-w-0 flex-1 flex-col">
        <div class="flex items-start justify-between gap-space-xs">
          <h2 class="min-w-0 break-words font-headline-md text-headline-md leading-tight text-on-secondary">
            {{ name }}
          </h2>
          <button
            type="button"
            aria-label="Редактировать профиль"
            class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-on-secondary/15 transition-transform hover:bg-on-secondary/25 active:scale-95"
            @click="$emit('edit')"
          >
            <MsIcon name="settings" :size="18" />
          </button>
        </div>

        <p class="mt-0.5 font-body-sm text-body-sm leading-snug text-secondary-fixed-dim">
          {{ roleTitle(profile.role) }}
        </p>

        <div class="mt-space-xs flex flex-wrap items-center gap-space-xs">
          <span
            v-if="profile.city"
            class="inline-flex min-w-0 max-w-full items-center gap-1 rounded-full bg-on-secondary/15 px-2 py-0.5 font-label-sm text-label-sm text-on-secondary"
          >
            <MsIcon name="location_on" :size="12" />
            <span class="truncate">{{ profile.city }}</span>
          </span>
          <span
            v-if="profile.squad_id"
            class="inline-flex items-center gap-1 rounded-full bg-on-secondary/15 px-2 py-0.5 font-label-sm text-label-sm text-on-secondary"
          >
            <MsIcon name="groups" :size="12" />
            В отряде
          </span>
          <span v-if="since" class="font-label-sm text-label-sm text-secondary-fixed-dim">в экспедиции с {{ since }}</span>
        </div>
      </div>
    </div>

    <p
      v-if="profile.bio"
      class="relative z-10 whitespace-pre-line break-words font-body-sm text-body-sm leading-snug text-secondary-fixed-dim"
    >
      {{ profile.bio }}
    </p>

    <!--
      Сводка не плашка внутри плашки: карточка и так выделена цветом, а вторая
      заливка поверх неё дробила бы её на «коробки». Строки держит одна линия
      сверху и разделители между ними.
    -->
    <dl class="relative z-10 divide-y divide-on-secondary/10 border-t border-on-secondary/15">
      <div v-if="email" class="flex items-center justify-between gap-space-sm py-space-sm">
        <dt class="flex shrink-0 items-center gap-space-xs font-label-sm text-label-sm text-secondary-fixed-dim">
          <MsIcon name="mail" :size="15" />
          Почта
        </dt>
        <dd class="min-w-0 truncate font-label-md text-label-md text-on-secondary">{{ email }}</dd>
      </div>

      <div class="flex items-center justify-between gap-space-sm py-space-sm">
        <dt class="flex shrink-0 items-center gap-space-xs font-label-sm text-label-sm text-secondary-fixed-dim">
          <MsIcon name="notifications" :size="15" />
          Находки рядом
        </dt>
        <dd class="min-w-0 text-right font-label-md text-label-md text-on-secondary">
          <template v-if="profile.subscribed_to_search">{{ profile.alert_radius_km }} км</template>
          <span v-else class="text-secondary-fixed-dim">выключены</span>
        </dd>
      </div>

      <div
        v-if="profile.home_lat !== null && profile.home_lon !== null"
        class="flex items-center justify-between gap-space-sm py-space-sm"
      >
        <dt class="flex shrink-0 items-center gap-space-xs font-label-sm text-label-sm text-secondary-fixed-dim">
          <MsIcon name="home_pin" :size="15" />
          Домашняя точка
        </dt>
        <dd class="min-w-0 text-right font-label-md text-label-md tabular-nums text-on-secondary">
          {{ profile.home_lat.toFixed(3) }}, {{ profile.home_lon.toFixed(3) }}
        </dd>
      </div>
    </dl>

  </article>
</template>
