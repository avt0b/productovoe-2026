<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { opsApi } from '@/api/endpoints'
import type { RouteItem } from '@/api/types'
import PageHeader from '@/components/PageHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useResourceList } from '@/composables/useResourceList'
import { errorText } from '@/lib'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const publishedFilter = ref('')
const modeFilter = ref('')
const query = ref('')
const actionError = ref<string | null>(null)
const pending = ref<string | null>(null)

const list = useResourceList<RouteItem>((limit, offset) =>
  opsApi.routes({
    is_published: publishedFilter.value === '' ? undefined : publishedFilter.value === 'true',
    mode: modeFilter.value || undefined,
    query: query.value || undefined,
    limit,
    offset,
  }),
)

async function togglePublish(route: RouteItem): Promise<void> {
  pending.value = route.id
  actionError.value = null
  try {
    await opsApi.publishRoute(route.id, !route.is_published)
    await list.load()
  } catch (e) {
    // Бэкенд не даст опубликовать маршрут без точек — показываем его причину.
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
      eyebrow="Семейный навигатор"
      title="Квест-маршруты"
      subtitle="Черновики видны только автору. Опубликованный маршрут появляется у семей в приложении."
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
          placeholder="Поиск по названию или городу"
          @keyup.enter="list.reload"
        />
      </div>
      <select v-model="publishedFilter" class="field lg:w-56" @change="list.reload">
        <option value="">Все маршруты</option>
        <option value="true">Опубликованные</option>
        <option value="false">Черновики</option>
      </select>
      <select v-model="modeFilter" class="field lg:w-56" @change="list.reload">
        <option value="">Любой режим</option>
        <option value="family">Семейный</option>
        <option value="general">Обычный</option>
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
      empty-text="Маршрутов нет"
      empty-icon="route"
      @retry="list.load"
    >
      <div class="overflow-hidden rounded-xl bg-surface-container-low shadow-sm">
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead class="table-head">
              <tr>
                <th>Маршрут</th>
                <th>Город</th>
                <th>Режим</th>
                <th>Длина</th>
                <th>Статус</th>
                <th class="text-right">Действия</th>
              </tr>
            </thead>
            <tbody class="font-body-md text-body-md">
              <tr v-for="route in list.items.value" :key="route.id" class="table-row">
                <td>
                  <div class="flex flex-col">
                    <span class="font-medium text-on-surface">{{ route.title }}</span>
                    <span class="line-clamp-1 font-body-sm text-body-sm text-on-surface-variant">
                      {{ route.description || 'Без описания' }}
                    </span>
                  </div>
                </td>
                <td class="text-on-surface-variant">{{ route.city || '—' }}</td>
                <td>
                  <StatusBadge
                    :label="route.mode === 'family' ? 'Семейный' : 'Обычный'"
                    :tone="route.mode === 'family' ? 'info' : 'neutral'"
                  />
                </td>
                <td class="mono whitespace-nowrap">{{ route.distance_km.toFixed(1) }} км</td>
                <td>
                  <StatusBadge
                    :label="route.is_published ? 'Опубликован' : 'Черновик'"
                    :tone="route.is_published ? 'verified' : 'pending'"
                  />
                </td>
                <td class="text-right">
                  <button
                    class="btn-secondary btn-sm"
                    type="button"
                    :disabled="!auth.canWrite || pending === route.id"
                    @click="togglePublish(route)"
                  >
                    {{
                      pending === route.id
                        ? '…'
                        : route.is_published
                          ? 'Снять с публикации'
                          : 'Опубликовать'
                    }}
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
  </div>
</template>
