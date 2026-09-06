<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { opsApi } from '@/api/endpoints'
import type { NeedStatus, Squad, SquadNeed, Trip } from '@/api/types'
import ModalDialog from '@/components/ModalDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { errorText, formatDate, formatMoney, formatNumber } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

type Tab = 'squads' | 'needs' | 'trips'
const tab = ref<Tab>('needs')

const TABS: Array<{ value: Tab; label: string; icon: string }> = [
  { value: 'needs', label: 'Потребности и сборы', icon: 'volunteer_activism' },
  { value: 'squads', label: 'Поисковые отряды', icon: 'groups' },
  { value: 'trips', label: 'Выезды', icon: 'calendar_month' },
]

const NEED_KINDS: Record<string, string> = {
  volunteers: 'Люди',
  funds: 'Деньги',
  equipment: 'Снаряжение',
}

const needStatus = ref<NeedStatus | ''>('open')
const upcomingOnly = ref(true)
const query = ref('')

const squads = useResourceList<Squad>((limit, offset) =>
  opsApi.squads({ query: query.value || undefined, limit, offset }),
)
const needs = useResourceList<SquadNeed>((limit, offset) =>
  opsApi.needs({ status: needStatus.value || undefined, limit, offset }),
)
const trips = useResourceList<Trip>((limit, offset) =>
  opsApi.trips({ upcoming_only: upcomingOnly.value, limit, offset }),
)

const closeTarget = ref<SquadNeed | null>(null)
const reason = ref('')
const busy = ref(false)
const actionError = ref<string | null>(null)

/** Прогресс денежного сбора; для людей и снаряжения — та же логика по штукам. */
function progress(need: SquadNeed): number {
  if (!need.target_amount) return 0
  return Math.min(100, Math.round((need.collected_amount / need.target_amount) * 100))
}

function amount(need: SquadNeed): string {
  const collected = need.kind === 'funds' ? formatMoney(need.collected_amount) : formatNumber(need.collected_amount)
  const target =
    need.target_amount === null
      ? 'без цели'
      : need.kind === 'funds'
        ? formatMoney(need.target_amount)
        : formatNumber(need.target_amount)
  return `${collected} из ${target}`
}

function openClose(need: SquadNeed): void {
  closeTarget.value = need
  reason.value = ''
  actionError.value = null
}

async function closeNeed(): Promise<void> {
  const need = closeTarget.value
  if (!need) return
  busy.value = true
  actionError.value = null
  try {
    await opsApi.closeNeed(need.id, reason.value.trim())
    closeTarget.value = null
    await needs.load()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    busy.value = false
  }
}

function loadActive(): void {
  if (tab.value === 'squads') void squads.load()
  else if (tab.value === 'needs') void needs.load()
  else void trips.load()
}

watch(tab, loadActive)
onMounted(loadActive)
</script>

<template>
  <div class="flex flex-col gap-space-6">
    <PageHeader
      eyebrow="Поисковый штаб"
      title="Отряды, сборы и выезды"
      subtitle="Потребности отрядов: люди на раскопки, целевые сборы на ГСМ и снаряжение, календарь «Выходных с поисковиком»."
    />

    <div class="flex flex-wrap items-center gap-space-1 rounded-lg bg-surface-container-high p-space-1">
      <button
        v-for="item in TABS"
        :key="item.value"
        class="flex h-10 items-center gap-space-2 rounded px-space-5 font-label-action text-label-action uppercase tracking-wider transition-colors"
        :class="
          tab === item.value
            ? 'bg-primary text-on-primary shadow-sm'
            : 'text-on-surface-variant hover:text-on-surface'
        "
        type="button"
        @click="tab = item.value"
      >
        <span class="ms-icon text-[18px]">{{ item.icon }}</span>
        {{ item.label }}
      </button>
    </div>

    <!-- Потребности и сборы -->
    <template v-if="tab === 'needs'">
      <div class="card flex flex-col items-stretch gap-space-3 lg:flex-row lg:items-center">
        <select v-model="needStatus" class="field lg:w-64" @change="needs.reload">
          <option value="">Все</option>
          <option value="open">Открытые</option>
          <option value="closed">Закрытые</option>
        </select>
      </div>

      <StateBlock
        :loading="needs.loading.value"
        :error="needs.error.value"
        :empty="needs.items.value.length === 0"
        empty-text="Потребностей нет"
        empty-icon="volunteer_activism"
        @retry="needs.load"
      >
        <div class="grid grid-cols-1 gap-card-gap lg:grid-cols-2">
          <article v-for="need in needs.items.value" :key="need.id" class="card flex flex-col gap-space-3">
            <div class="card-header-strip">
              <span class="font-bold text-primary">{{ NEED_KINDS[need.kind] ?? need.kind }}</span>
              <span>{{ formatDate(need.created_at) }}</span>
            </div>

            <div class="flex flex-col gap-space-1">
              <h3 class="font-headline-sm text-headline-sm uppercase text-on-surface">
                {{ need.title }}
              </h3>
              <p class="line-clamp-2 font-body-sm text-body-sm text-on-surface-variant">
                {{ need.description || 'Без описания' }}
              </p>
            </div>

            <div class="flex flex-col gap-space-1">
              <div class="flex items-center justify-between">
                <span class="font-label-action text-label-action text-on-surface">
                  {{ amount(need) }}
                </span>
                <StatusBadge
                  :label="need.status === 'open' ? 'Открыт' : 'Закрыт'"
                  :tone="need.status === 'open' ? 'info' : 'neutral'"
                />
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-surface-container-high">
                <div class="h-full rounded-full bg-secondary" :style="{ width: `${progress(need)}%` }" />
              </div>
            </div>

            <div class="mt-auto flex items-center justify-between pt-space-2">
              <span class="mono text-outline">отряд {{ need.squad_id.slice(0, 8) }}</span>
              <button
                v-if="need.status === 'open'"
                class="btn-secondary btn-sm"
                type="button"
                :disabled="!auth.canWrite"
                @click="openClose(need)"
              >
                Закрыть сбор
              </button>
            </div>
          </article>
        </div>

        <div class="mt-space-4 overflow-hidden rounded-xl bg-surface-container-low">
          <PaginationBar
            :total="needs.total.value"
            :limit="needs.limit.value"
            :offset="needs.offset.value"
            @update:offset="needs.setOffset"
          />
        </div>
      </StateBlock>
    </template>

    <!-- Отряды -->
    <template v-else-if="tab === 'squads'">
      <div class="card flex flex-col items-stretch gap-space-3 lg:flex-row lg:items-center">
        <div class="relative flex-1">
          <span class="ms-icon absolute left-space-3 top-1/2 -translate-y-1/2 text-[20px] text-outline">
            search
          </span>
          <input
            v-model="query"
            class="field pl-10"
            type="search"
            placeholder="Поиск по названию или региону"
            @keyup.enter="squads.reload"
          />
        </div>
        <button class="btn-primary" type="button" @click="squads.reload">Найти</button>
      </div>

      <StateBlock
        :loading="squads.loading.value"
        :error="squads.error.value"
        :empty="squads.items.value.length === 0"
        empty-text="Отрядов нет"
        empty-icon="groups"
        @retry="squads.load"
      >
        <div class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="table-head">
                <tr>
                  <th>Отряд</th>
                  <th>Регион</th>
                  <th>Контакт</th>
                  <th>Создан</th>
                </tr>
              </thead>
              <tbody class="font-body-md text-body-md">
                <tr v-for="squad in squads.items.value" :key="squad.id" class="table-row">
                  <td>
                    <div class="flex flex-col">
                      <span class="font-medium text-on-surface">{{ squad.name }}</span>
                      <span class="line-clamp-1 font-body-sm text-body-sm text-on-surface-variant">
                        {{ squad.description }}
                      </span>
                    </div>
                  </td>
                  <td class="text-on-surface-variant">{{ squad.region || '—' }}</td>
                  <td class="mono text-secondary">{{ squad.contact || '—' }}</td>
                  <td class="mono whitespace-nowrap text-on-surface-variant">
                    {{ formatDate(squad.created_at) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <PaginationBar
            :total="squads.total.value"
            :limit="squads.limit.value"
            :offset="squads.offset.value"
            @update:offset="squads.setOffset"
          />
        </div>
      </StateBlock>
    </template>

    <!-- Выезды -->
    <template v-else>
      <div class="card flex items-center gap-space-3">
        <label class="flex cursor-pointer items-center gap-space-2">
          <input v-model="upcomingOnly" type="checkbox" @change="trips.reload" />
          <span class="font-label-action text-label-action uppercase text-on-surface">
            Только предстоящие
          </span>
        </label>
      </div>

      <StateBlock
        :loading="trips.loading.value"
        :error="trips.error.value"
        :empty="trips.items.value.length === 0"
        empty-text="Выездов нет"
        empty-icon="event_busy"
        @retry="trips.load"
      >
        <div class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead class="table-head">
                <tr>
                  <th>Дата</th>
                  <th>Выезд</th>
                  <th>Место</th>
                  <th>Мест всего</th>
                </tr>
              </thead>
              <tbody class="font-body-md text-body-md">
                <tr v-for="trip in trips.items.value" :key="trip.id" class="table-row">
                  <td class="mono whitespace-nowrap text-primary">{{ formatDate(trip.starts_on) }}</td>
                  <td class="font-medium">{{ trip.title }}</td>
                  <td class="text-on-surface-variant">{{ trip.location || '—' }}</td>
                  <td class="mono">{{ trip.capacity }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <PaginationBar
            :total="trips.total.value"
            :limit="trips.limit.value"
            :offset="trips.offset.value"
            @update:offset="trips.setOffset"
          />
        </div>
      </StateBlock>
    </template>

    <ModalDialog
      v-if="closeTarget"
      title="Закрытие сбора"
      icon="lock"
      :busy="busy"
      @close="closeTarget = null"
    >
      <div class="flex flex-col gap-space-3">
        <div class="rounded-lg bg-surface-container p-space-3">
          <span class="field-label">Сбор</span>
          <span class="font-headline-sm text-headline-sm uppercase text-on-surface">
            {{ closeTarget.title }}
          </span>
          <span class="block font-body-sm text-body-sm text-on-surface-variant">
            {{ amount(closeTarget) }}
          </span>
        </div>
        <div>
          <label class="field-label" for="need-reason">Основание</label>
          <textarea
            id="need-reason"
            v-model="reason"
            class="field h-auto py-space-2"
            rows="3"
            placeholder="Например: цель достигнута, отчёт о тратах опубликован"
          />
        </div>
        <p v-if="actionError" class="font-body-sm text-body-sm text-error">{{ actionError }}</p>
      </div>
      <template #actions>
        <button class="btn-primary" type="button" :disabled="busy" @click="closeNeed">
          {{ busy ? 'Закрываем…' : 'Закрыть сбор' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>
