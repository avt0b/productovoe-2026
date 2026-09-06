<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { opsApi } from '@/api/endpoints'
import type { ArchiveEntry, EntryKind, EntryStatus } from '@/api/types'
import ModalDialog from '@/components/ModalDialog.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { coords, errorText, formatDate } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const KINDS: Record<string, string> = {
  event: 'Событие',
  soldier_card: 'Карточка бойца',
  memory: 'Воспоминание',
  photo_story: 'Фото и история',
}

const STATUS_TONE = { pending: 'pending', verified: 'verified', rejected: 'error' } as const
const STATUS_LABEL = {
  pending: 'Ожидает проверки',
  verified: 'Подтверждено',
  rejected: 'Отклонено',
} as const

const statusFilter = ref<EntryStatus | ''>('pending')
const kindFilter = ref<EntryKind | ''>('')
const query = ref('')

const list = useResourceList<ArchiveEntry>((limit, offset) =>
  opsApi.entries({
    status: statusFilter.value || undefined,
    kind: kindFilter.value || undefined,
    query: query.value || undefined,
    limit,
    offset,
  }),
)

const selected = ref<ArchiveEntry | null>(null)
const decision = ref<'verify' | 'reject'>('verify')
const note = ref('')
const busy = ref(false)
const actionError = ref<string | null>(null)

function review(entry: ArchiveEntry, action: 'verify' | 'reject'): void {
  selected.value = entry
  decision.value = action
  note.value = ''
  actionError.value = null
}

async function submit(): Promise<void> {
  const entry = selected.value
  if (!entry) return
  if (!note.value.trim()) {
    actionError.value = 'Укажите обоснование — оно попадёт в журнал и в карточку записи'
    return
  }
  busy.value = true
  actionError.value = null
  try {
    if (decision.value === 'verify') await opsApi.verifyEntry(entry.id, note.value.trim())
    else await opsApi.rejectEntry(entry.id, note.value.trim())
    selected.value = null
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
      eyebrow="Народный архив"
      title="Модерация заявок"
      subtitle="Записи, предложенные пользователями. Подтверждение означает, что сведения сверены с источником."
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
          placeholder="Поиск по заголовку записи"
          @keyup.enter="list.reload"
        />
      </div>
      <select v-model="statusFilter" class="field lg:w-56" @change="list.reload">
        <option value="">Любой статус</option>
        <option value="pending">Ожидают проверки</option>
        <option value="verified">Подтверждённые</option>
        <option value="rejected">Отклонённые</option>
      </select>
      <select v-model="kindFilter" class="field lg:w-56" @change="list.reload">
        <option value="">Все типы</option>
        <option v-for="(label, value) in KINDS" :key="value" :value="value">{{ label }}</option>
      </select>
      <button class="btn-primary" type="button" @click="list.reload">Найти</button>
    </div>

    <StateBlock
      :loading="list.loading.value"
      :error="list.error.value"
      :empty="list.items.value.length === 0"
      empty-text="Очередь пуста — все заявки разобраны"
      empty-icon="task_alt"
      @retry="list.load"
    >
      <div class="grid grid-cols-1 gap-card-gap xl:grid-cols-2">
        <article v-for="entry in list.items.value" :key="entry.id" class="card flex flex-col gap-space-3">
          <div class="card-header-strip">
            <span class="font-bold text-primary">{{ KINDS[entry.kind] ?? entry.kind }}</span>
            <span>{{ formatDate(entry.created_at) }}</span>
          </div>

          <div class="flex flex-col gap-space-1">
            <h3 class="font-body-memorial-name text-body-memorial-name text-on-surface">
              {{ entry.title }}
            </h3>
            <p class="line-clamp-3 font-body-md text-body-md text-on-surface-variant">
              {{ entry.body || 'Описание не заполнено' }}
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-space-3">
            <StatusBadge :label="STATUS_LABEL[entry.status]" :tone="STATUS_TONE[entry.status]" />
            <span v-if="entry.lat !== null && entry.lon !== null" class="mono text-secondary">
              <span class="ms-icon align-middle text-[14px]">pin_drop</span>
              {{ coords(entry.lat, entry.lon) }}
            </span>
            <span v-else class="mono text-outline">без геопривязки</span>
            <span v-if="entry.date_text" class="mono text-on-surface-variant">
              {{ entry.date_text }}
            </span>
          </div>

          <div v-if="entry.review_note" class="rounded-lg bg-surface-container p-space-3">
            <span class="field-label">Заключение проверяющего</span>
            <p class="font-body-sm text-body-sm text-on-surface">{{ entry.review_note }}</p>
          </div>

          <div class="mt-auto flex items-center justify-between gap-space-2 pt-space-2">
            <span class="mono text-outline">автор {{ entry.submitted_by.slice(0, 8) }}</span>
            <div v-if="entry.status === 'pending'" class="flex items-center gap-space-2">
              <button
                class="btn-ghost btn-sm text-error"
                type="button"
                :disabled="!auth.canWrite"
                @click="review(entry, 'reject')"
              >
                Отклонить
              </button>
              <button
                class="btn-primary btn-sm"
                type="button"
                :disabled="!auth.canWrite"
                @click="review(entry, 'verify')"
              >
                <span class="ms-icon text-[16px]">verified</span>
                Подтвердить
              </button>
            </div>
          </div>
        </article>
      </div>

      <div class="mt-space-4 overflow-hidden rounded-xl bg-surface-container-low">
        <PaginationBar
          :total="list.total.value"
          :limit="list.limit.value"
          :offset="list.offset.value"
          @update:offset="list.setOffset"
        />
      </div>
    </StateBlock>

    <ModalDialog
      v-if="selected"
      :title="decision === 'verify' ? 'Подтверждение записи' : 'Отклонение записи'"
      :icon="decision === 'verify' ? 'verified' : 'cancel'"
      :tone="decision === 'verify' ? 'primary' : 'danger'"
      :busy="busy"
      @close="selected = null"
    >
      <div class="flex flex-col gap-space-3">
        <div class="rounded-lg bg-surface-container p-space-3">
          <span class="field-label">Запись</span>
          <span class="font-body-memorial-name text-body-memorial-name text-on-surface">
            {{ selected.title }}
          </span>
        </div>
        <div>
          <label class="field-label" for="note">
            Обоснование со ссылкой на источник — обязательно
          </label>
          <textarea
            id="note"
            v-model="note"
            class="field h-auto py-space-2"
            rows="4"
            placeholder="Например: сверено с Книгой Памяти Орловской обл., Т. 5, с. 123; геопривязка подтверждена протоколом отряда «Высота»"
          />
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Решение и обоснование сохраняются в карточке записи и в журнале аудита.
        </p>
        <p v-if="actionError" class="font-body-sm text-body-sm text-error">{{ actionError }}</p>
      </div>
      <template #actions>
        <button
          :class="decision === 'verify' ? 'btn-primary' : 'btn-danger'"
          type="button"
          :disabled="busy"
          @click="submit"
        >
          {{ busy ? 'Сохраняем…' : decision === 'verify' ? 'Подтвердить' : 'Отклонить' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>
