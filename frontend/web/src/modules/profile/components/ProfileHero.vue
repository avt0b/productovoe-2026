<script setup>
import { computed } from 'vue'
import SmartImage from '@shared/components/SmartImage.vue'

// Карточка-шапка профиля: карточка на пергаменте, а не цветной баннер;
// аватар с бейджем «подтверждён»; строка роли; три счётчика снизу. Все
// поля — настоящие данные профиля, ничего не выдумано.
const props = defineProps({
  name: { type: String, default: '' },
  role: { type: String, default: '' },
  city: { type: String, default: '' },
  avatarUrl: { type: String, default: '' },
  verified: { type: Boolean, default: false },
  since: { type: String, default: '' },
  routesCompleted: { type: Number, default: 0 },
  excursionsCompleted: { type: Number, default: 0 },
  findsCount: { type: Number, default: 0 },
})

const sinceLabel = computed(() => {
  if (!props.since) return ''
  const date = new Date(props.since)
  if (Number.isNaN(date.getTime())) return ''
  const month = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' }).format(date).replace(/^\d+\s*/, '')
  return `В проекте с ${month} ${date.getFullYear()}`
})

const counters = computed(() => [
  { value: props.routesCompleted, label: 'маршрутов пройдено' },
  { value: props.excursionsCompleted, label: 'экскурсий' },
  { value: props.findsCount, label: 'находок проверено', accent: true },
])
</script>

<template>
  <section class="flex flex-col gap-6 rounded-2xl bg-surface-container-lowest p-6 shadow-document mb-8">
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-5">
      <div class="relative shrink-0">
        <div class="w-16 h-16 rounded-full overflow-hidden bg-secondary-container text-on-secondary-container">
          <SmartImage :src="avatarUrl" icon="person" img-class="w-full h-full object-cover" />
        </div>
        <span
          v-if="verified"
          class="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-tertiary text-on-tertiary ring-2 ring-surface-container-lowest"
          title="Профиль подтверждён"
        >
          <span class="material-symbols-outlined text-[15px]" style="font-variation-settings: 'FILL' 1">verified</span>
        </span>
      </div>

      <div class="flex flex-col min-w-0 flex-1 gap-0.5">
        <p class="font-archival text-archival uppercase text-on-surface-variant">
          {{ role || 'Исследователь' }}{{ verified ? ' · подтверждён' : '' }}
        </p>
        <h1 class="font-headline-lg text-headline-lg text-on-surface [overflow-wrap:anywhere]">{{ name || 'Без имени' }}</h1>
        <div v-if="city || sinceLabel" class="mt-1 flex flex-wrap items-center gap-2">
          <span
            v-if="city"
            class="flex items-center gap-1 rounded-full bg-surface-container-high px-2 py-0.5 font-label-sm text-label-sm text-on-surface"
          >
            <span class="material-symbols-outlined text-[15px]">location_on</span>
            {{ city }}
          </span>
          <span v-if="sinceLabel" class="font-label-sm text-label-sm text-on-surface-variant">{{ sinceLabel }}</span>
        </div>
      </div>
    </div>

    <dl class="grid grid-cols-3 divide-x divide-outline-variant/60">
      <div v-for="counter in counters" :key="counter.label" class="flex flex-col items-center justify-end gap-1 px-1 text-center">
        <dd class="font-headline-md text-headline-md" :class="counter.accent ? 'text-tertiary' : 'text-on-surface'">
          {{ counter.value }}
        </dd>
        <dt class="font-label-sm text-label-sm leading-tight text-on-surface-variant">{{ counter.label }}</dt>
      </div>
    </dl>
  </section>
</template>
