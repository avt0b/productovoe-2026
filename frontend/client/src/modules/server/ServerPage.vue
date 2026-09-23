<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import {
  SERVICE_NAMES,
  SERVICE_TITLES,
  normalizeOrigin,
  resolveServiceUrl,
  serverChoice,
  serverLabel,
  setServerChoice,
  type ServerChoice,
  type ServerMode,
} from '@/core/server'
import { useSessionStore } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'

import { probeAll, readRecent, rememberRecent, type ProbeResult } from './probe'

const router = useRouter()
const session = useSessionStore()

const MODES: readonly { value: ServerMode; title: string; hint: string }[] = [
  { value: 'ports', title: 'Порты 8001–8007', hint: 'Сервисы запущены по отдельности — локальная разработка' },
  { value: 'gateway', title: 'Шлюз /api', hint: 'Один адрес, сервисы за nginx' },
]

/** Адрес без `http://` — так его привычнее читать и править. */
function display(origin: string): string {
  return origin.replace(/^http:\/\//, '')
}

const mode = ref<ServerMode>(serverChoice.value?.mode ?? 'ports')
const address = ref(serverChoice.value ? display(serverChoice.value.origin) : '')
const results = ref<ProbeResult[] | null>(null)
const checking = ref(false)
const saving = ref(false)

const origin = computed(() => normalizeOrigin(address.value))
const candidate = computed<ServerChoice | null>(() => (origin.value ? { mode: mode.value, origin: origin.value } : null))
const current = computed(() => serverLabel())

// Поменяли адрес или режим — прошлая проверка уже не про него.
watch(candidate, () => (results.value = null))

/** Подсказки: этот компьютер, компьютер, с которого открыта страница, недавние адреса. */
const suggestions = computed(() => {
  const list = ['127.0.0.1']
  const host = window.location.hostname
  // В APK страница открыта с https://localhost — это сам телефон, а не сервер.
  if (window.location.protocol === 'http:' && host && host !== 'localhost' && host !== '127.0.0.1') list.push(host)
  for (const recent of readRecent()) list.push(display(recent))
  return [...new Set(list)]
})

/** Адреса сервисов при введённом сервере — видно, куда именно пойдут запросы. */
const preview = computed(() =>
  SERVICE_NAMES.map((service) => {
    const probed = results.value?.find((result) => result.service === service)
    return {
      service,
      title: SERVICE_TITLES[service],
      url: candidate.value ? resolveServiceUrl(candidate.value, service) : '—',
      state: probed?.state ?? null,
      detail: probed?.detail ?? '',
    }
  }),
)

const downCount = computed(() => results.value?.filter((result) => result.state === 'down').length ?? 0)

const STATE_ICON = {
  ok: { name: 'check_circle', class: 'text-secondary' },
  error: { name: 'warning', class: 'text-tertiary' },
  down: { name: 'cancel', class: 'text-error' },
} as const

async function check(): Promise<void> {
  if (!candidate.value || checking.value) return
  checking.value = true
  try {
    results.value = await probeAll(candidate.value)
  } finally {
    checking.value = false
  }
}

function sameAsCurrent(next: ServerChoice | null): boolean {
  const now = serverChoice.value
  if (!now || !next) return now === next
  return now.mode === next.mode && now.origin === next.origin
}

/**
 * Применить выбор. Токены одного сервера на другом недействительны, поэтому
 * сессия закрывается — на старом сервере, пока выбор ещё не сменился.
 */
async function apply(next: ServerChoice | null): Promise<void> {
  if (saving.value) return
  saving.value = true
  try {
    if (!sameAsCurrent(next)) {
      if (session.isAuthenticated) await session.signOut()
      setServerChoice(next)
      if (next) rememberRecent(next.origin)
    }
    await router.replace(router.hasRoute('auth') && !session.isAuthenticated ? { name: 'auth' } : { name: 'home' })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin pb-space-xl pt-space-sm">
    <InlineNotice icon="science">
      Экран для тестов: к какому бэкенду подключаться. После смены сервера нужно войти заново. Перед релизом экран
      уберём.
    </InlineNotice>

    <div class="flex items-center gap-space-sm rounded-lg bg-surface-container-low p-space-md">
      <MsIcon name="dns" :size="22" class="shrink-0 text-secondary" />
      <div class="min-w-0">
        <span class="block font-label-sm text-label-sm text-outline">Сейчас</span>
        <span class="block truncate font-label-lg text-label-lg text-on-surface">{{ current }}</span>
      </div>
    </div>

    <fieldset class="flex flex-col gap-space-sm">
      <legend class="mb-1 font-label-md text-label-md text-on-surface">Как подняты сервисы</legend>
      <div class="grid grid-cols-2 gap-space-sm">
        <button
          v-for="option in MODES"
          :key="option.value"
          type="button"
          class="flex flex-col items-start gap-0.5 rounded-DEFAULT p-space-sm text-left transition-colors"
          :class="mode === option.value ? 'bg-secondary text-on-secondary' : 'bg-surface-container-low text-on-surface'"
          :aria-pressed="mode === option.value"
          @click="mode = option.value"
        >
          <span class="font-label-lg text-label-lg">{{ option.title }}</span>
          <span class="font-body-sm text-body-sm opacity-80">{{ option.hint }}</span>
        </button>
      </div>
    </fieldset>

    <form class="flex flex-col gap-space-sm" @submit.prevent="check">
      <FormInput
        v-model="address"
        label="Адрес компьютера или шлюза"
        type="text"
        inputmode="url"
        placeholder="192.168.1.10"
        :hint="mode === 'ports' ? 'Только адрес: порты сервисов подставятся сами' : 'Например, https://marshruty.ru'"
      />

      <div class="flex flex-wrap gap-space-xs">
        <button
          v-for="suggestion in suggestions"
          :key="suggestion"
          type="button"
          class="rounded-full bg-surface-container px-3 py-1.5 font-label-md text-label-md text-on-surface-variant hover:bg-surface-container-high"
          @click="address = suggestion"
        >
          {{ suggestion }}
        </button>
      </div>

      <p v-if="address && !origin" class="font-body-sm text-body-sm text-error" role="alert">
        Не получилось разобрать адрес — нужен вид 192.168.1.10 или https://example.ru
      </p>

      <div class="grid grid-cols-2 gap-space-sm pt-space-xs">
        <button
          type="submit"
          class="flex items-center justify-center gap-1.5 rounded-full bg-secondary-container py-3 font-label-lg text-label-lg text-on-secondary-container active:scale-[0.99] disabled:opacity-60"
          :disabled="!candidate || checking"
        >
          <MsIcon :name="checking ? 'progress_activity' : 'network_check'" :size="20" :class="{ 'animate-spin': checking }" />
          Проверить
        </button>
        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full bg-primary py-3 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
          :disabled="!candidate || saving"
          @click="apply(candidate)"
        >
          <MsIcon name="save" :size="20" />
          Подключиться
        </button>
      </div>
    </form>

    <section class="flex flex-col gap-space-xs rounded-lg bg-surface-container-lowest p-space-md shadow-sm">
      <h2 class="font-label-lg text-label-lg text-on-surface">Куда пойдут запросы</h2>
      <ul class="flex flex-col divide-y divide-surface-container">
        <li v-for="row in preview" :key="row.service" class="flex items-center gap-space-sm py-2">
          <MsIcon
            :name="row.state ? STATE_ICON[row.state].name : 'radio_button_unchecked'"
            :size="20"
            class="shrink-0"
            :class="row.state ? STATE_ICON[row.state].class : 'text-outline'"
          />
          <div class="min-w-0 flex-1">
            <span class="block font-label-md text-label-md text-on-surface">{{ row.title }}</span>
            <span class="block truncate font-mono text-label-sm text-outline">{{ row.url }}</span>
          </div>
          <span v-if="row.detail" class="shrink-0 font-label-sm text-label-sm text-on-surface-variant">{{ row.detail }}</span>
        </li>
      </ul>
    </section>

    <InlineNotice v-if="downCount > 0" tone="error" icon="lan">
      Не ответили {{ downCount }} из {{ SERVICE_NAMES.length }}. Проверьте: сервис запущен с
      <code>--host 0.0.0.0</code>, порт открыт в брандмауэре, телефон в той же сети, а адрес приложения есть в
      <code>CORS_ORIGINS</code> сервиса (у APK — <code>https://localhost</code>).
    </InlineNotice>

    <button
      v-if="serverChoice"
      type="button"
      class="flex items-center justify-center gap-1.5 rounded-full bg-surface-container-high py-3 font-label-lg text-label-lg text-on-surface active:scale-[0.99] disabled:opacity-60"
      :disabled="saving"
      @click="apply(null)"
    >
      <MsIcon name="restart_alt" :size="20" />
      Вернуть адреса из сборки
    </button>
  </div>
</template>
