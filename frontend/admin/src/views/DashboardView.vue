<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { dashboardApi } from '@/api/endpoints'
import type { DashboardOverview, HealthReport, Timeseries } from '@/api/types'
import PageHeader from '@/components/PageHeader.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatTile from '@/components/StatTile.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import TrendChart from '@/components/TrendChart.vue'
import { errorText, formatDateTime } from '@/lib'

const overview = ref<DashboardOverview | null>(null)
const series = ref<Timeseries | null>(null)
const health = ref<HealthReport | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const days = ref(30)

const TILE_ICONS: Record<string, string> = {
  users_total: 'group',
  role_verification_queue: 'badge',
  moderation_queue: 'rule',
  last_stand_points: 'pin_drop',
  active_expeditions: 'explore',
  media_queue: 'movie',
}

const SERVICE_TITLES: Record<string, string> = {
  ingest_service: 'Импорт архивов (Книги Памяти)',
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    // Три независимых запроса — грузим параллельно, а не по цепочке.
    const [overviewData, seriesData, healthData] = await Promise.all([
      dashboardApi.overview(8),
      dashboardApi.timeseries(days.value),
      dashboardApi.health(),
    ])
    overview.value = overviewData
    series.value = seriesData
    health.value = healthData
  } catch (e) {
    error.value = errorText(e)
  } finally {
    loading.value = false
  }
}

async function changeRange(value: number): Promise<void> {
  days.value = value
  try {
    series.value = await dashboardApi.timeseries(value)
  } catch (e) {
    error.value = errorText(e)
  }
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-space-8">
    <PageHeader
      eyebrow="Сводный мониторинг платформы"
      title="Панель оперативного администрирования"
      subtitle="Состояние сервисов, очереди модерации и последние действия администраторов"
    >
      <template #actions>
        <span
          v-if="overview"
          class="font-label-archive-code text-label-archive-code uppercase text-on-surface-variant"
        >
          Обновлено {{ formatDateTime(overview.generated_at) }}
        </span>
        <button class="btn-secondary" type="button" :disabled="loading" @click="load">
          <span class="ms-icon text-[18px]">refresh</span>
          Обновить
        </button>
      </template>
    </PageHeader>

    <StateBlock :loading="loading" :error="error" @retry="load">
      <div v-if="overview" class="flex flex-col gap-space-8">
        <!-- Предупреждение о недоступных сервисах -->
        <div
          v-if="overview.degraded.length"
          class="flex items-start gap-space-3 rounded-xl bg-tertiary-fixed p-space-4 text-on-tertiary-fixed"
        >
          <span class="ms-icon text-[20px]">warning</span>
          <div class="flex flex-col">
            <span class="font-label-action text-label-action uppercase">
              Часть сервисов недоступна — показатели по ним не собраны
            </span>
            <span class="font-body-sm text-body-sm">{{ overview.degraded.join(', ') }}</span>
          </div>
        </div>

        <!-- Плитки KPI -->
        <div class="grid grid-cols-1 gap-card-gap sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <StatTile
            v-for="tile in overview.tiles"
            :key="tile.key"
            :label="tile.label"
            :value="tile.value"
            :hint="tile.hint"
            :tone="tile.tone"
            :icon="TILE_ICONS[tile.key] ?? 'analytics'"
          />
        </div>

        <div class="grid grid-cols-1 gap-space-6 lg:grid-cols-12">
          <!-- График -->
          <section class="card flex flex-col gap-space-4 lg:col-span-8">
            <div class="flex flex-wrap items-center justify-between gap-space-3">
              <div class="flex flex-col">
                <span
                  class="font-label-archive-code text-label-archive-code uppercase tracking-wider text-primary"
                >
                  Динамика за период
                </span>
                <h2 class="font-headline-md text-headline-md uppercase text-on-surface">
                  Внесение и проверка записей
                </h2>
              </div>
              <div class="flex items-center gap-space-1 rounded-lg bg-surface-container p-1">
                <button
                  v-for="option in [7, 30, 90]"
                  :key="option"
                  class="rounded px-space-3 py-1 font-label-action text-label-action uppercase transition-colors"
                  :class="
                    days === option
                      ? 'bg-primary text-on-primary'
                      : 'text-on-surface-variant hover:text-on-surface'
                  "
                  type="button"
                  @click="changeRange(option)"
                >
                  {{ option }} дн.
                </button>
              </div>
            </div>
            <TrendChart v-if="series" :series="series.series" />
          </section>

          <!-- Состояние сервисов -->
          <section class="card flex flex-col gap-space-3 lg:col-span-4">
            <div class="flex items-center justify-between">
              <h2 class="font-headline-sm text-headline-sm uppercase text-on-surface">
                Состояние сервисов
              </h2>
              <StatusBadge
                v-if="health"
                :label="`${health.healthy} / ${health.total}`"
                :tone="health.healthy === health.total ? 'verified' : 'pending'"
              />
            </div>

            <div v-if="health" class="flex flex-col gap-space-2">
              <div
                v-for="row in health.services"
                :key="row.service"
                class="flex items-center justify-between rounded-lg bg-surface-container px-space-3 py-space-2"
              >
                <div class="flex min-w-0 flex-col">
                  <span class="truncate font-label-action text-label-action text-on-surface">
                    {{ row.title }}
                  </span>
                  <span class="mono truncate text-on-surface-variant">{{ row.service }}</span>
                </div>
                <span
                  class="h-2.5 w-2.5 shrink-0 rounded-full"
                  :class="row.ok ? 'bg-verified' : 'bg-error'"
                  :title="row.status"
                />
              </div>
            </div>

            <div
              v-if="overview.not_implemented.length"
              class="mt-space-2 rounded-lg bg-surface-container p-space-3"
            >
              <span class="field-label">Ещё не реализовано в бэкенде</span>
              <ul class="flex flex-col gap-1">
                <li
                  v-for="name in overview.not_implemented"
                  :key="name"
                  class="font-body-sm text-body-sm text-on-surface-variant"
                >
                  · {{ SERVICE_TITLES[name] ?? name }}
                </li>
              </ul>
            </div>
          </section>
        </div>

        <!-- Журнал последних действий -->
        <section class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
          <div class="flex items-center justify-between p-card-padding">
            <div class="flex flex-col">
              <span
                class="font-label-archive-code text-label-archive-code uppercase tracking-wider text-primary"
              >
                Протокол аудита
              </span>
              <h2 class="font-headline-md text-headline-md uppercase text-on-surface">
                Последние действия администраторов
              </h2>
            </div>
            <RouterLink class="btn-secondary btn-sm" :to="{ name: 'audit' }">
              Весь журнал
              <span class="ms-icon text-[16px]">arrow_forward</span>
            </RouterLink>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="table-head">
                <tr>
                  <th>Время</th>
                  <th>Администратор</th>
                  <th>Действие</th>
                  <th>Объект</th>
                  <th>Результат</th>
                </tr>
              </thead>
              <tbody class="font-body-sm text-body-sm">
                <tr v-if="!overview.recent_audit.length">
                  <td colspan="5" class="px-space-4 py-space-6 text-center text-on-surface-variant">
                    Действий пока не было
                  </td>
                </tr>
                <tr v-for="row in overview.recent_audit" :key="row.id" class="table-row">
                  <td class="mono whitespace-nowrap text-on-surface-variant">
                    {{ formatDateTime(row.created_at) }}
                  </td>
                  <td class="whitespace-nowrap font-medium">{{ row.actor_email }}</td>
                  <td class="mono text-primary">{{ row.action }}</td>
                  <td class="max-w-[320px] truncate" :title="row.message">
                    {{ row.target_label || row.target_id || '—' }}
                  </td>
                  <td>
                    <StatusBadge
                      :label="row.outcome === 'success' ? 'Выполнено' : 'Отказ'"
                      :tone="row.outcome === 'success' ? 'verified' : 'error'"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </StateBlock>
  </div>
</template>
