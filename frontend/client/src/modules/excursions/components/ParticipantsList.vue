<script setup lang="ts">
import { computed } from 'vue'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { Participant } from '../data'

/**
 * Кто записан — экран краеведа.
 *
 * Краеведу важно знать не число, а состав: придёт ли класс с сопровождающими
 * и сколько их. Сервис отдаёт этот список только ведущему экскурсии.
 */
const props = defineProps<{ participants: Participant[] }>()

/** Заявки от школ и клубов — наверх: к ним готовятся отдельно. */
const rows = computed(() =>
  [...props.participants].sort((a, b) => Number(Boolean(b.organization_name)) - Number(Boolean(a.organization_name))),
)

const total = computed(() => props.participants.reduce((sum, row) => sum + Math.max(1, row.group_size), 0))
</script>

<template>
  <section class="flex flex-col gap-space-xs">
    <h3 class="font-archival text-archival uppercase text-on-surface-variant">
      Записаны: {{ total }} {{ plural(total, ['человек', 'человека', 'человек']) }}
    </h3>

    <ul class="flex flex-col gap-1">
      <li
        v-for="row in rows"
        :key="row.id"
        class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-sm shadow-document"
      >
        <span
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
          :class="row.organization_name ? 'bg-secondary-fixed text-secondary' : 'bg-surface-container-high text-on-surface-variant'"
        >
          <MsIcon :name="row.organization_name ? 'school' : 'person'" :size="18" />
        </span>
        <span class="min-w-0 flex-1">
          <span class="block truncate font-label-lg text-label-lg text-on-surface">
            {{ row.organization_name || 'Отдельный участник' }}
          </span>
          <span class="block font-body-sm text-body-sm text-on-surface-variant">
            {{ row.group_size }} {{ plural(row.group_size, ['человек', 'человека', 'человек']) }}
            <template v-if="row.checked_in_at"> · на месте</template>
          </span>
        </span>
        <MsIcon v-if="row.checked_in_at" name="task_alt" :size="20" class="shrink-0 text-secondary" aria-label="Отметился" />
      </li>
    </ul>
  </section>
</template>
