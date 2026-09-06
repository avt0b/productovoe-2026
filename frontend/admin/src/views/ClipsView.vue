<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { opsApi } from '@/api/endpoints'
import type { Clip, ClipStatus } from '@/api/types'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { errorText, formatDateTime, soldierName } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const STATUS_LABEL: Record<ClipStatus, string> = {
  queued: 'В очереди',
  processing: 'Генерация',
  ready: 'Готово',
  failed: 'Ошибка',
}
const STATUS_TONE = {
  queued: 'pending',
  processing: 'info',
  ready: 'verified',
  failed: 'error',
} as const

const statusFilter = ref<ClipStatus | ''>('')
const query = ref('')
const pending = ref<string | null>(null)
const actionError = ref<string | null>(null)

const list = useResourceList<Clip>((limit, offset) =>
  opsApi.clips({
    status: statusFilter.value || undefined,
    query: query.value || undefined,
    limit,
    offset,
  }),
)

async function retry(clip: Clip): Promise<void> {
  pending.value = clip.id
  actionError.value = null
  try {
    await opsApi.retryClip(clip.id)
    await list.load()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    pending.value = null
  }
}

async function toggleVisibility(clip: Clip): Promise<void> {
  pending.value = clip.id
  actionError.value = null
  try {
    await opsApi.setClipVisibility(clip.id, !clip.is_public, 'Решение модератора мемориала')
    await list.load()
  } catch (e) {
    actionError.value = errorText(e)
  } finally {
    pending.value = null
  }
}

onMounted(list.load)
</script>

<template>
  <div class="flex flex-col gap-space-6">
    <PageHeader
      eyebrow="Модуль «Живое фото»"
      title="Очередь оживления фотографий"
      subtitle="Заявки на анимацию портретов бойцов. Технология применяется только в мемориальных целях."
    />

    <div
      class="flex items-start gap-space-3 rounded-xl bg-surface-container p-space-4 text-on-surface-variant"
    >
      <span class="ms-icon text-[20px] text-tertiary">policy</span>
      <p class="font-body-sm text-body-sm">
        Публикация в общем мемориале возможна только с согласия автора заявки. Снимайте с
        публикации всё, что искажает смысл высказывания или используется вне памяти о погибшем.
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
          placeholder="Поиск по имени бойца"
          @keyup.enter="list.reload"
        />
      </div>
      <select v-model="statusFilter" class="field lg:w-56" @change="list.reload">
        <option value="">Все статусы</option>
        <option value="queued">В очереди</option>
        <option value="processing">Генерация</option>
        <option value="ready">Готовые</option>
        <option value="failed">С ошибкой</option>
      </select>
      <button class="btn-primary" type="button" @click="list.reload">Найти</button>
    </div>

    <p
      v-if="actionError"
      class="rounded-lg bg-error-container px-space-4 py-space-3 font-body-sm text-body-sm text-on-error-container"
      role="alert"
    >
      {{ actionError }}
    </p>

    <StateBlock
      :loading="list.loading.value"
      :error="list.error.value"
      :empty="list.items.value.length === 0"
      empty-text="Заявок нет"
      empty-icon="movie"
      @retry="list.load"
    >
      <div class="grid grid-cols-1 gap-card-gap lg:grid-cols-2 xl:grid-cols-3">
        <article v-for="clip in list.items.value" :key="clip.id" class="card flex flex-col gap-space-3">
          <div class="card-header-strip">
            <span>{{ formatDateTime(clip.created_at) }}</span>
            <StatusBadge :label="STATUS_LABEL[clip.status]" :tone="STATUS_TONE[clip.status]" />
          </div>

          <h3 class="font-body-memorial-name text-body-memorial-name text-primary">
            {{ soldierName(clip.soldier_name) }}
          </h3>

          <blockquote
            class="rounded-lg bg-surface-container p-space-3 font-body-memorial-quote text-body-sm italic text-on-surface-variant"
          >
            {{ clip.narration_text }}
          </blockquote>

          <p v-if="clip.error" class="font-body-sm text-body-sm text-error">
            <span class="ms-icon align-middle text-[14px]">error</span>
            {{ clip.error }}
          </p>

          <div class="mt-auto flex items-center justify-between gap-space-2 pt-space-2">
            <StatusBadge
              :label="clip.is_public ? 'В мемориале' : 'Не опубликован'"
              :tone="clip.is_public ? 'info' : 'neutral'"
            />
            <div class="flex items-center gap-space-2">
              <button
                v-if="clip.status === 'failed'"
                class="btn-secondary btn-sm"
                type="button"
                :disabled="!auth.canWrite || pending === clip.id"
                @click="retry(clip)"
              >
                <span class="ms-icon text-[16px]">refresh</span>
                Повторить
              </button>
              <button
                v-if="clip.status === 'ready'"
                class="btn-sm"
                :class="clip.is_public ? 'btn-ghost text-error' : 'btn-secondary'"
                type="button"
                :disabled="!auth.canWrite || pending === clip.id"
                @click="toggleVisibility(clip)"
              >
                {{ clip.is_public ? 'Снять' : 'Опубликовать' }}
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
  </div>
</template>
