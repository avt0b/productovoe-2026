<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { listMyRoutes, type RouteDetail, type RouteSummary } from '@/core/services/routes'
import { can, useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import StateBlock from '@/ui/StateBlock.vue'

import AutoRouteSheet from './components/AutoRouteSheet.vue'
import RouteFormSheet from './components/RouteFormSheet.vue'

/**
 * Маршруты краеведа: черновики и опубликованные.
 *
 * Черновик видит только автор — пока в маршруте нет точек, сервис его и не
 * опубликует. Поэтому экран ведёт от создания к редактору, а не наоборот.
 */
const router = useRouter()
const session = useSessionStore()

const canAuthor = computed(() => session.hasAccount && can.authorRoute(session.user))

const { data, loading, error, retry } = useAsync<RouteSummary[]>(() => (canAuthor.value ? listMyRoutes() : Promise.resolve([])))

const creating = ref(false)
const generating = ref(false)

const drafts = computed(() => (data.value ?? []).filter((route) => !route.is_published))
const published = computed(() => (data.value ?? []).filter((route) => route.is_published))

function open(routeId: string): void {
  void router.push({ name: 'route-editor', params: { routeId } })
}

function onCreated(route: RouteSummary | RouteDetail): void {
  open(route.id)
}
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin short:gap-space-sm">
    <AccountRequired v-if="!session.hasAccount" text="Маршруты ведут из аккаунта краеведа" />

    <InlineNotice v-else-if="!canAuthor" tone="info">
      Вести маршруты могут краеведы. Подайте заявку на роль в профиле — её подтверждает
      администратор платформы.
    </InlineNotice>

    <template v-else>
      <div class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
        <p class="font-archival text-archival uppercase text-on-surface-variant">Маршруты краеведа</p>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Черновик видите только вы. Добавьте точки с рассказом и заданиями — и публикуйте: маршрут появится у семей.
        </p>
        <div class="flex flex-wrap gap-space-xs">
          <button
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-primary-container px-space-md py-2 font-label-md text-label-md text-white shadow-stamp active:scale-95"
            @click="creating = true"
          >
            <MsIcon name="add" :size="18" />
            Создать маршрут
          </button>
          <button
            type="button"
            class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
            @click="generating = true"
          >
            <MsIcon name="auto_awesome" :size="18" />
            Собрать по точкам рядом
          </button>
        </div>
      </div>

      <StateBlock
        v-if="loading || error"
        :loading="loading"
        :error="error"
        empty-icon="route"
        empty-text="Маршрутов пока нет"
        @retry="retry"
      />

      <template v-else>
        <section v-if="drafts.length" class="flex flex-col gap-space-sm">
          <h2 class="font-headline-md text-headline-md text-on-surface">Черновики</h2>
          <button
            v-for="route in drafts"
            :key="route.id"
            type="button"
            class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md text-left shadow-document active:scale-[0.99]"
            @click="open(route.id)"
          >
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-container-high text-on-surface-variant"
              aria-hidden="true"
            >
              <MsIcon name="edit_note" :size="20" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-headline-sm text-headline-sm text-on-surface">{{ route.title }}</span>
              <span class="block truncate font-body-sm text-body-sm text-on-surface-variant">
                {{ [route.city, route.mode === 'family' ? 'семейный' : 'общий'].filter(Boolean).join(' · ') }}
              </span>
            </span>
            <MsIcon name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
          </button>
        </section>

        <section v-if="published.length" class="flex flex-col gap-space-sm">
          <h2 class="font-headline-md text-headline-md text-on-surface">Опубликованные</h2>
          <button
            v-for="route in published"
            :key="route.id"
            type="button"
            class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md text-left shadow-document active:scale-[0.99]"
            @click="open(route.id)"
          >
            <span
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container"
              aria-hidden="true"
            >
              <MsIcon name="route" :size="20" />
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate font-headline-sm text-headline-sm text-on-surface">{{ route.title }}</span>
              <span class="block truncate font-body-sm text-body-sm text-on-surface-variant">
                {{ [route.city, route.distance_km ? `${route.distance_km} км` : ''].filter(Boolean).join(' · ') }}
              </span>
            </span>
            <MsIcon name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
          </button>
        </section>

        <StateBlock
          v-if="!drafts.length && !published.length"
          :loading="false"
          :error="null"
          empty
          empty-icon="route"
          empty-text="Маршрутов пока нет — создайте первый или соберите черновик по точкам рядом"
        />
      </template>
    </template>

    <RouteFormSheet v-if="creating" :route="null" @close="creating = false" @saved="onCreated" />
    <AutoRouteSheet v-if="generating" @close="generating = false" @created="onCreated" />
  </div>
</template>
