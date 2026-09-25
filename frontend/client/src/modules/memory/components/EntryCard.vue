<script setup lang="ts">
import { computed, ref } from 'vue'

import { formatCoordinates } from '@/core/geo'
import MsIcon from '@/ui/MsIcon.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { ENTRY_KINDS, ENTRY_STATUS, type ArchiveEntry } from '../data'

/**
 * Запись народного архива. `mine` — своя запись: видно, на какой она стадии и
 * что написал проверяющий. `reviewable` — краевед проверяет чужую запись.
 */
const props = defineProps<{
  entry: ArchiveEntry
  mine?: boolean
  reviewable?: boolean
  busy?: boolean
  /** Сюда только что привели — карточку надо заметить. */
  focused?: boolean
}>()

const emit = defineEmits<{ review: [verdict: 'verify' | 'reject', note: string]; edit: []; remove: [] }>()

const expanded = ref(false)
const rejecting = ref(false)
const removing = ref(false)
const note = ref('')

/**
 * Свою запись автор правит и убирает, пока она на проверке: подтверждённую
 * меняет уже краевед (`update`/`delete` в archive_service).
 */
const canEdit = computed(() => props.mine === true && props.entry.status === 'pending')

const longBody = props.entry.body.length > 220
</script>

<template>
  <article
    class="flex scroll-mt-space-md flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document ring-tertiary/60 transition-shadow duration-300"
    :class="{ 'ring-2': focused }"
  >
    <div class="flex items-center justify-between gap-space-xs">
      <span class="flex min-w-0 items-center gap-1 font-archival text-archival uppercase text-on-surface-variant">
        <MsIcon :name="ENTRY_KINDS[entry.kind].icon" :size="15" class="shrink-0" />
        <span class="truncate">{{ ENTRY_KINDS[entry.kind].title }}</span>
      </span>
      <span
        v-if="mine || reviewable || entry.status === 'verified'"
        class="flex shrink-0 items-center gap-1 rounded-full px-2.5 py-0.5 font-label-sm text-label-sm"
        :class="ENTRY_STATUS[entry.status].class"
      >
        <MsIcon :name="ENTRY_STATUS[entry.status].icon" :size="15" :filled="entry.status === 'verified'" />
        {{ ENTRY_STATUS[entry.status].title }}
      </span>
    </div>

    <div>
      <h3 class="font-headline-sm text-headline-sm text-on-surface">{{ entry.title }}</h3>
      <p v-if="entry.date_text" class="font-label-md text-label-md text-on-surface-variant">{{ entry.date_text }}</p>
    </div>

    <template v-if="entry.body">
      <p
        class="whitespace-pre-line font-body-sm text-body-sm text-on-surface-variant"
        :class="{ 'line-clamp-4': longBody && !expanded }"
      >
        {{ entry.body }}
      </p>
      <button
        v-if="longBody"
        type="button"
        class="-mt-space-xs self-start font-label-md text-label-md text-secondary"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        {{ expanded ? 'Свернуть' : 'Читать полностью' }}
      </button>
    </template>

    <img v-if="entry.media_url" :src="entry.media_url" alt="" class="max-h-56 w-full rounded-2xl object-cover" loading="lazy" />

    <p v-if="entry.lat !== null && entry.lon !== null" class="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
      <MsIcon name="pin_drop" :size="15" class="shrink-0" />
      {{ formatCoordinates({ lat: entry.lat, lon: entry.lon }) }}
    </p>

    <div v-if="mine && entry.review_note" class="flex flex-col gap-0.5 rounded-2xl bg-surface-container-low px-space-sm py-2">
      <span class="font-archival text-archival uppercase text-on-surface-variant">Комментарий проверяющего</span>
      <p class="font-body-sm text-body-sm text-on-surface">{{ entry.review_note }}</p>
    </div>

    <div v-if="canEdit" class="flex flex-col gap-space-xs pt-space-xs">
      <div class="flex flex-wrap gap-space-xs">
        <button
          type="button"
          class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
          @click="emit('edit')"
        >
          <MsIcon name="edit" :size="18" />
          Изменить
        </button>
        <button
          type="button"
          class="rounded-full px-space-md py-2 font-label-md text-label-md text-error active:scale-95"
          :aria-expanded="removing"
          @click="removing = !removing"
        >
          Убрать запись
        </button>
      </div>
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="removing ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!removing"
      >
        <div class="overflow-hidden">
          <div
            class="flex items-center justify-between gap-space-sm rounded-2xl bg-surface-container-low px-space-sm py-2"
            role="alertdialog"
            aria-label="Подтверждение удаления записи"
          >
            <span class="min-w-0 font-body-sm text-body-sm text-on-surface">Убрать запись из архива? Это не отменить.</span>
            <div class="flex shrink-0 gap-space-xs">
              <button
                type="button"
                class="rounded-full px-space-sm py-1.5 font-label-md text-label-md text-on-surface-variant active:scale-95"
                @click="removing = false"
              >
                Нет
              </button>
              <button
                type="button"
                class="rounded-full bg-error px-space-sm py-1.5 font-label-md text-label-md text-on-error active:scale-95 disabled:opacity-60"
                :disabled="busy"
                @click="emit('remove')"
              >
                Убрать
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="reviewable" class="flex flex-col pt-space-xs">
      <div class="grid grid-cols-2 gap-space-sm">
        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full bg-tertiary py-2.5 font-label-md text-label-md text-on-tertiary transition-all active:scale-[0.99] disabled:opacity-60"
          :disabled="busy"
          @click="emit('review', 'verify', '')"
        >
          <MsIcon :name="busy && !rejecting ? 'progress_activity' : 'verified'" :size="18" :class="{ 'animate-spin': busy && !rejecting }" filled />
          Подтвердить
        </button>
        <button
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-full py-2.5 font-label-md text-label-md transition-colors duration-200 active:scale-[0.99] disabled:opacity-60"
          :class="rejecting ? 'bg-inverse-surface text-inverse-on-surface' : 'bg-surface-container-high text-on-surface'"
          :disabled="busy"
          :aria-expanded="rejecting"
          @click="rejecting = !rejecting"
        >
          <MsIcon name="block" :size="18" />
          Отклонить
        </button>
      </div>

      <!-- Причина отказа раскрывается под кнопками: автор увидит её у себя в «Моих записях». -->
      <div
        class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
        :class="rejecting ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
        :inert="!rejecting"
      >
        <form class="flex flex-col gap-space-sm overflow-hidden" @submit.prevent="emit('review', 'reject', note.trim())">
          <div class="pt-space-sm">
            <FormTextarea
              v-model="note"
              label="Почему отклонено"
              :rows="2"
              :maxlength="1000"
              placeholder="Не нашли в Книге Памяти, нужны документы…"
              hint="Автор увидит комментарий и сможет дополнить запись"
            />
          </div>
          <button
            type="submit"
            class="flex items-center justify-center gap-1.5 rounded-full bg-inverse-surface py-2.5 font-label-md text-label-md text-inverse-on-surface active:scale-[0.99] disabled:opacity-60"
            :disabled="busy"
          >
            <MsIcon v-if="busy" name="progress_activity" :size="18" class="animate-spin" />
            Отклонить запись
          </button>
        </form>
      </div>
    </div>
  </article>
</template>
