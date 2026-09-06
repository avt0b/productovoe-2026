<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { auditApi } from '@/api/endpoints'
import type { AuditEntry } from '@/api/types'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { formatDateTime } from '@/lib'

const query = ref('')
const serviceFilter = ref('')
const outcomeFilter = ref('')
const daysFilter = ref('')

const SERVICES: Record<string, string> = {
  auth_service: 'Аутентификация',
  user_service: 'Профили',
  map_service: 'Карта',
  route_service: 'Маршруты',
  search_hq_service: 'Поисковый штаб',
  archive_service: 'Народный архив',
  media_service: '«Живое фото»',
}

const OUTCOMES = { success: 'Выполнено', denied: 'Отказано', failed: 'Ошибка' } as const
const OUTCOME_TONE = { success: 'verified', denied: 'pending', failed: 'error' } as const

const expanded = ref<string | null>(null)

const list = useResourceList<AuditEntry>(
  (limit, offset) =>
    auditApi.list({
      query: query.value || undefined,
      target_service: serviceFilter.value || undefined,
      outcome: outcomeFilter.value || undefined,
      days: daysFilter.value ? Number(daysFilter.value) : undefined,
      limit,
      offset,
    }),
  30,
)

function toggle(id: string): void {
  expanded.value = expanded.value === id ? null : id
}

onMounted(list.load)
</script>

<template>
  <div class="flex flex-col gap-space-6">
    <PageHeader
      eyebrow="Протокол аудита"
      title="Журнал действий администраторов"
      subtitle="Записи не редактируются и не удаляются: должно быть видно, кто и на каком основании изменил данные о погибшем."
    />

    <div class="card flex flex-col items-stretch gap-space-3 lg:flex-row lg:items-center">
      <div class="relative flex-1">
        <span class="ms-icon absolute left-space-3 top-1/2 -translate-y-1/2 text-[20px] text-outline">
          search
        </span>
        <input
          v-model="query"
          class="field pl-10"
          type="search"
          placeholder="Поиск по объекту или администратору"
          @keyup.enter="list.reload"
        />
      </div>
      <select v-model="serviceFilter" class="field lg:w-56" @change="list.reload">
        <option value="">Все сервисы</option>
        <option v-for="(label, value) in SERVICES" :key="value" :value="value">{{ label }}</option>
      </select>
      <select v-model="outcomeFilter" class="field lg:w-48" @change="list.reload">
        <option value="">Любой результат</option>
        <option value="success">Выполнено</option>
        <option value="denied">Отказано</option>
        <option value="failed">Ошибка</option>
      </select>
      <select v-model="daysFilter" class="field lg:w-48" @change="list.reload">
        <option value="">За всё время</option>
        <option value="1">За сутки</option>
        <option value="7">За неделю</option>
        <option value="30">За месяц</option>
      </select>
      <button class="btn-primary" type="button" @click="list.reload">Найти</button>
    </div>

    <StateBlock
      :loading="list.loading.value"
      :error="list.error.value"
      :empty="list.items.value.length === 0"
      empty-text="Записей по заданным условиям нет"
      empty-icon="history"
      @retry="list.load"
    >
      <div class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead class="table-head">
              <tr>
                <th>Время</th>
                <th>Администратор</th>
                <th>Действие</th>
                <th>Объект</th>
                <th>Результат</th>
                <th class="w-10" />
              </tr>
            </thead>
            <tbody class="font-body-sm text-body-sm">
              <template v-for="row in list.items.value" :key="row.id">
                <tr class="table-row cursor-pointer" @click="toggle(row.id)">
                  <td class="mono whitespace-nowrap text-on-surface-variant">
                    {{ formatDateTime(row.created_at) }}
                  </td>
                  <td class="whitespace-nowrap">
                    <div class="flex flex-col">
                      <span class="font-medium text-on-surface">{{ row.actor_email }}</span>
                      <span class="mono text-outline">{{ row.actor_role }}</span>
                    </div>
                  </td>
                  <td class="mono whitespace-nowrap text-primary">{{ row.action }}</td>
                  <td class="max-w-[340px]">
                    <div class="flex flex-col">
                      <span class="truncate text-on-surface">{{ row.target_label || '—' }}</span>
                      <span class="mono truncate text-outline">
                        {{ SERVICES[row.target_service] ?? row.target_service }}
                      </span>
                    </div>
                  </td>
                  <td>
                    <StatusBadge :label="OUTCOMES[row.outcome]" :tone="OUTCOME_TONE[row.outcome]" />
                  </td>
                  <td class="text-right text-on-surface-variant">
                    <span class="ms-icon text-[18px]">
                      {{ expanded === row.id ? 'expand_less' : 'expand_more' }}
                    </span>
                  </td>
                </tr>
                <tr v-if="expanded === row.id" class="bg-surface-container/60">
                  <td colspan="6" class="px-space-4 py-space-3">
                    <div class="flex flex-col gap-space-2">
                      <div v-if="row.message">
                        <span class="field-label">Обоснование</span>
                        <p class="font-body-md text-body-md text-on-surface">{{ row.message }}</p>
                      </div>
                      <div class="grid grid-cols-1 gap-space-3 sm:grid-cols-3">
                        <div>
                          <span class="field-label">Идентификатор объекта</span>
                          <span class="mono text-on-surface">{{ row.target_id || '—' }}</span>
                        </div>
                        <div>
                          <span class="field-label">IP администратора</span>
                          <span class="mono text-on-surface">{{ row.ip || '—' }}</span>
                        </div>
                        <div>
                          <span class="field-label">Тип объекта</span>
                          <span class="mono text-on-surface">{{ row.target_type || '—' }}</span>
                        </div>
                      </div>
                      <div v-if="Object.keys(row.payload).length">
                        <span class="field-label">Изменение</span>
                        <pre
                          class="overflow-x-auto rounded-lg bg-surface-container-lowest p-space-3 font-label-archive-code text-label-archive-code text-on-surface"
                          >{{ JSON.stringify(row.payload, null, 2) }}</pre
                        >
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
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
  </div>
</template>
