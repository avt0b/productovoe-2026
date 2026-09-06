<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { opsApi } from '@/api/endpoints'
import type { LastStandPoint, LastStandStatus } from '@/api/types'
import ModalDialog from '@/components/ModalDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { coords, errorText, formatDate, soldierName } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const STATUSES: Array<{ value: LastStandStatus; label: string; hint: string }> = [
  {
    value: 'discovered',
    label: 'Обнаружено место',
    hint: 'Заявлено поисковиком или краеведом, требуется проверка по архиву',
  },
  {
    value: 'archive_confirmed',
    label: 'Подтверждено архивом',
    hint: 'Сведения сверены с Книгой Памяти или донесением о потерях',
  },
  {
    value: 'remains_raised',
    label: 'Останки подняты',
    hint: 'Работы завершены, захоронение состоялось',
  },
]

const STATUS_LABEL: Record<LastStandStatus, string> = {
  discovered: 'Обнаружено',
  archive_confirmed: 'Подтверждено архивом',
  remains_raised: 'Останки подняты',
}
const STATUS_TONE = {
  discovered: 'error',
  archive_confirmed: 'info',
  remains_raised: 'verified',
} as const

const statusFilter = ref<LastStandStatus | ''>('')
const query = ref('')

const list = useResourceList<LastStandPoint>((limit, offset) =>
  opsApi.lastStand({
    status: statusFilter.value || undefined,
    query: query.value || undefined,
    limit,
    offset,
  }),
)

const target = ref<LastStandPoint | null>(null)
const nextStatus = ref<LastStandStatus>('discovered')
const reason = ref('')
const busy = ref(false)
const actionError = ref<string | null>(null)

function openStatus(point: LastStandPoint): void {
  target.value = point
  nextStatus.value = point.status
  reason.value = ''
  actionError.value = null
}

async function saveStatus(): Promise<void> {
  const point = target.value
  if (!point) return
  busy.value = true
  actionError.value = null
  try {
    await opsApi.setLastStandStatus(point.id, nextStatus.value, reason.value.trim())
    target.value = null
    await list.load()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    busy.value = false
  }
}

onMounted(list.load)
</script>

<template>
  <div class="flex flex-col gap-space-6">
    <PageHeader
      eyebrow="Модуль «Последний бой»"
      title="Места гибели красноармейцев"
      subtitle="Красные метки — заявлено, но не подтверждено архивом. Зелёные — работы завершены."
    />

    <div
      class="flex items-start gap-space-3 rounded-xl bg-surface-container p-space-4 text-on-surface-variant"
    >
      <span class="ms-icon text-[20px] text-primary">shield</span>
      <p class="font-body-sm text-body-sm">
        Точные координаты неподнятых останков — наводка для нелегальных раскопок. Ограничение
        публичной точности в бэкенде пока не реализовано: в модели точки нет флага геомаскирования.
        До этого момента экспорт и публикация координат остаются на ответственности администратора.
      </p>
    </div>

    <div class="card flex flex-col items-stretch gap-space-3 lg:flex-row lg:items-center">
      <div class="relative flex-1">
        <span class="ms-icon absolute left-space-3 top-1/2 -translate-y-1/2 text-[20px] text-outline">
          search
        </span>
        <input
          v-model="query"
          class="field pl-10"
          type="search"
          placeholder="Поиск по ФИО бойца или воинской части"
          @keyup.enter="list.reload"
        />
      </div>
      <select v-model="statusFilter" class="field lg:w-64" @change="list.reload">
        <option value="">Все статусы</option>
        <option v-for="s in STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
      <button class="btn-primary" type="button" @click="list.reload">Найти</button>
    </div>

    <StateBlock
      :loading="list.loading.value"
      :error="list.error.value"
      :empty="list.items.value.length === 0"
      empty-text="Точек по заданным условиям нет"
      empty-icon="location_off"
      @retry="list.load"
    >
      <div class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead class="table-head">
              <tr>
                <th>Боец</th>
                <th>Воинская часть</th>
                <th>Координаты</th>
                <th>Статус</th>
                <th>Заявлено</th>
                <th class="text-right">Действия</th>
              </tr>
            </thead>
            <tbody class="font-body-md text-body-md">
              <tr v-for="point in list.items.value" :key="point.id" class="table-row">
                <td>
                  <div class="flex flex-col">
                    <span class="font-body-memorial-name text-body-memorial-name text-primary">
                      {{ soldierName(point.soldier_name) }}
                    </span>
                    <span v-if="point.date_text" class="mono text-on-surface-variant">
                      {{ point.date_text }}
                    </span>
                  </div>
                </td>
                <td class="text-on-surface-variant">{{ point.unit || '—' }}</td>
                <td class="mono whitespace-nowrap text-secondary">
                  {{ coords(point.lat, point.lon) }}
                </td>
                <td>
                  <StatusBadge
                    :label="STATUS_LABEL[point.status]"
                    :tone="STATUS_TONE[point.status]"
                  />
                </td>
                <td class="mono whitespace-nowrap text-on-surface-variant">
                  {{ formatDate(point.created_at) }}
                </td>
                <td class="text-right">
                  <button
                    class="btn-secondary btn-sm"
                    type="button"
                    :disabled="!auth.canWrite"
                    @click="openStatus(point)"
                  >
                    Статус
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <PaginationBar
          :total="list.total.value"
          :limit="list.limit.value"
          :offset="list.offset.value"
          @update:offset="list.setOffset"
        />
      </div>
    </StateBlock>

    <ModalDialog
      v-if="target"
      title="Смена статуса точки"
      icon="flag"
      :busy="busy"
      @close="target = null"
    >
      <div class="flex flex-col gap-space-3">
        <div class="rounded-lg bg-surface-container p-space-3">
          <span class="field-label">Точка</span>
          <span class="font-body-memorial-name text-body-memorial-name text-on-surface">
            {{ soldierName(target.soldier_name) }}
          </span>
          <span class="mono block text-secondary">{{ coords(target.lat, target.lon) }}</span>
        </div>

        <label
          v-for="s in STATUSES"
          :key="s.value"
          class="flex cursor-pointer items-start gap-space-3 rounded-lg bg-surface-container p-space-3 hover:bg-surface-container-high"
        >
          <input v-model="nextStatus" class="mt-1" type="radio" :value="s.value" name="status" />
          <div class="flex flex-col">
            <span class="font-label-action text-label-action uppercase text-on-surface">
              {{ s.label }}
            </span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">{{ s.hint }}</span>
          </div>
        </label>

        <div>
          <label class="field-label" for="reason">Основание</label>
          <textarea
            id="reason"
            v-model="reason"
            class="field h-auto py-space-2"
            rows="3"
            placeholder="Ссылка на архивное дело, протокол экспедиции или Книгу Памяти"
          />
        </div>
        <p v-if="actionError" class="font-body-sm text-body-sm text-error">{{ actionError }}</p>
      </div>
      <template #actions>
        <button class="btn-primary" type="button" :disabled="busy" @click="saveStatus">
          {{ busy ? 'Сохраняем…' : 'Обновить статус' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>
