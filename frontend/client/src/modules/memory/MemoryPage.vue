<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import { can, useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import StateBlock from '@/ui/StateBlock.vue'

import ClipCard from './components/ClipCard.vue'
import ClipRequestSheet from './components/ClipRequestSheet.vue'
import EntryCard from './components/EntryCard.vue'
import LivingPortraitPlayer from './components/LivingPortraitPlayer.vue'
import ProposeEntrySheet from './components/ProposeEntrySheet.vue'
import ShareClipSheet from './components/ShareClipSheet.vue'
import {
  DEFAULT_NARRATION,
  ENTRY_KINDS,
  fetchMemorial,
  fetchModerationQueue,
  fetchMyClips,
  fetchMyEntries,
  fetchPublicEntries,
  retryClip,
  reviewEntry,
  type ArchiveEntry,
  type Clip,
  type EntryKind,
} from './data'

type Tab = 'photo' | 'archive' | 'review'
type Sheet = { kind: 'clip' } | { kind: 'propose'; entryKind: EntryKind } | { kind: 'share'; clip: Clip } | { kind: 'account'; text: string }

/**
 * Пример оформления, пока ни одного готового ролика нет: портрет из макета.
 * Подписан как пример — выдавать его за настоящего героя нельзя.
 */
const EXAMPLE_PORTRAIT =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuD2xyruqLOLailgDwisn_NnihcRFmdBlieraiQdmaqn0ppj6dkFlzXw6_Y7Y9K2rD4LRgGr9jB_ECv19-YEihit12h2WdRqODXXZE1czSNUvLTgTBbkRRzZ1i5Fm-3Poe33DEoMquYIhjDRZDedEY8deprL23qFYSthoaRgnLYbHYwjFMbG8uoeyFs-J7TLDluluY3_MUsv1VLoerDvDCfV-HfFNmiLSv5YZ19HHgFUY_1Ye3yNWfFK'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const canReview = computed(() => session.hasAccount && can.verifyArchive(session.user))
const TABS = computed(() => [
  { id: 'photo' as const, title: 'Живое фото', icon: 'auto_awesome' },
  { id: 'archive' as const, title: 'Народный архив', icon: 'menu_book' },
  ...(canReview.value ? [{ id: 'review' as const, title: 'Проверка', icon: 'fact_check' }] : []),
])

/** Вкладка — в адресе: из профиля «Добавить героя» ведёт сразу в архив с открытой формой. */
function tabFromQuery(): Tab {
  const tab = route.query.tab
  if (route.query.propose) return 'archive'
  return tab === 'archive' || (tab === 'review' && canReview.value) ? tab : 'photo'
}

const tab = ref<Tab>(tabFromQuery())
watch(tab, (value) => void router.replace({ query: { ...route.query, tab: value, propose: undefined } }))

const sheet = ref<Sheet | null>(null)
const notice = ref<{ tone: 'success' | 'error'; text: string } | null>(null)

const proposeKind = route.query.propose
if (typeof proposeKind === 'string' && proposeKind in ENTRY_KINDS) {
  sheet.value = session.hasAccount
    ? { kind: 'propose', entryKind: proposeKind as EntryKind }
    : { kind: 'account', text: 'Добавить героя в архив можно с аккаунтом' }
}

// --- живое фото ---

const photo = useAsync(async () => {
  const [memorial, mine] = await Promise.all([fetchMemorial(), session.hasAccount ? fetchMyClips() : Promise.resolve(null)])
  return { memorial, mine }
})
const selectedClipId = ref<string | null>(null)
const busyClipId = ref<string | null>(null)

/** Что показывает плеер: выбранный ролик, свой готовый, из мемориала — или пример. */
const shownClip = computed<Clip | null>(() => {
  const all = [...(photo.data.value?.mine ?? []), ...(photo.data.value?.memorial ?? [])].filter((clip) => clip.status === 'ready')
  return all.find((clip) => clip.id === selectedClipId.value) ?? all[0] ?? null
})

async function refreshPhoto(): Promise<void> {
  try {
    photo.data.value = {
      memorial: await fetchMemorial(),
      mine: session.hasAccount ? await fetchMyClips() : null,
    }
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  }
}

async function retry(clip: Clip): Promise<void> {
  busyClipId.value = clip.id
  try {
    await retryClip(clip.id)
    await refreshPhoto()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    busyClipId.value = null
  }
}

function openClipRequest(): void {
  sheet.value = session.hasAccount ? { kind: 'clip' } : { kind: 'account', text: 'Оживить фото можно с аккаунтом' }
}

async function clipCreated(): Promise<void> {
  sheet.value = null
  notice.value = { tone: 'success', text: 'Заявка принята и стоит в очереди на оживление' }
  await refreshPhoto()
}

// --- народный архив ---

const kindFilter = ref<EntryKind | null>(null)
const archive = useAsync(async () => {
  const [feed, mine] = await Promise.all([
    fetchPublicEntries(kindFilter.value),
    session.hasAccount ? fetchMyEntries() : Promise.resolve(null),
  ])
  return { feed, mine }
})
watch(kindFilter, () => void archive.retry())

/** Свои записи — все стадии; в общей ленте — только подтверждённые, без повторов своих. */
const myEntries = computed(() =>
  (archive.data.value?.mine ?? []).filter((entry) => !kindFilter.value || entry.kind === kindFilter.value),
)
const feed = computed(() => {
  const mine = new Set(myEntries.value.map((entry) => entry.id))
  return (archive.data.value?.feed ?? []).filter((entry) => !mine.has(entry.id))
})

function openPropose(entryKind: EntryKind = 'event'): void {
  sheet.value = session.hasAccount ? { kind: 'propose', entryKind } : { kind: 'account', text: 'Предложить запись можно с аккаунтом' }
}

async function entryCreated(entry: ArchiveEntry): Promise<void> {
  sheet.value = null
  tab.value = 'archive'
  notice.value = { tone: 'success', text: `«${entry.title}» отправлено краеведу на проверку` }
  await archive.retry()
}

// --- проверка краеведом ---

const queue = useAsync(async () => (canReview.value ? fetchModerationQueue() : []))
const busyEntryId = ref<string | null>(null)

async function review(entry: ArchiveEntry, verdict: 'verify' | 'reject', note: string): Promise<void> {
  busyEntryId.value = entry.id
  try {
    await reviewEntry(entry.id, verdict, note)
    queue.data.value = (queue.data.value ?? []).filter((item) => item.id !== entry.id)
    // Подтверждённая запись должна сразу появиться в ленте на соседней вкладке.
    void archive.retry()
    notice.value = {
      tone: 'success',
      text: verdict === 'verify' ? `«${entry.title}» подтверждено — запись появилась в ленте` : `«${entry.title}» отклонено`,
    }
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    busyEntryId.value = null
  }
}
</script>

<template>
  <div class="flex w-full flex-col space-y-space-md px-margin pb-8">
    <div class="flex flex-col space-y-space-xs pt-space-xs">
      <div class="inline-flex items-center gap-1.5 self-start rounded-full bg-secondary-container/60 px-3 py-1 text-on-secondary-container">
        <MsIcon name="auto_awesome" :size="16" filled />
        <span class="font-label-sm text-label-sm tracking-wide">Память поколений</span>
      </div>
      <h2 class="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">Живая память</h2>
      <p class="font-body-md text-body-md text-outline">Ожившие портреты героев и народный архив Орловщины</p>
    </div>

    <div class="grid gap-1 rounded-full bg-surface-container-low p-1" :class="TABS.length === 3 ? 'grid-cols-3' : 'grid-cols-2'" role="tablist">
      <button
        v-for="item in TABS"
        :key="item.id"
        type="button"
        role="tab"
        :aria-selected="tab === item.id"
        class="flex items-center justify-center gap-1 rounded-full py-2 font-label-md text-label-md transition-all"
        :class="tab === item.id ? 'bg-surface-container-lowest text-on-surface shadow-sm' : 'text-on-surface-variant'"
        @click="tab = item.id"
      >
        <MsIcon :name="item.icon" :size="16" />
        <span class="truncate">{{ item.title }}</span>
        <span v-if="item.id === 'review' && queue.data.value?.length" class="rounded-full bg-primary px-1.5 font-label-sm text-label-sm text-on-primary">
          {{ queue.data.value.length }}
        </span>
      </button>
    </div>

    <InlineNotice v-if="notice" :tone="notice.tone">{{ notice.text }}</InlineNotice>

    <!-- Живое фото -->
    <template v-if="tab === 'photo'">
      <!-- Этическая пометка: без неё реконструкцию легко принять за подлинную запись. -->
      <div class="flex items-start gap-3 rounded-lg bg-secondary-container/40 p-3.5 shadow-sm">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary-container text-secondary">
          <MsIcon name="shield_with_heart" :size="18" filled />
        </div>
        <p class="font-body-sm text-body-sm leading-snug text-on-secondary-container">
          Технология применяется только в мемориальных целях, с уважением к памяти защитников Отечества. Движение и
          голос — реконструкция по архивной фотографии.
        </p>
      </div>

      <StateBlock v-if="photo.loading.value || photo.error.value" :loading="photo.loading.value" :error="photo.error.value" @retry="photo.retry" />
      <template v-else>
        <LivingPortraitPlayer
          v-if="shownClip"
          :image="shownClip.source_photo_url"
          :video-url="shownClip.video_url"
          :line="shownClip.narration_text"
          :caption="shownClip.soldier_name || 'Живое фото'"
        />
        <LivingPortraitPlayer v-else :image="EXAMPLE_PORTRAIT" :line="DEFAULT_NARRATION" caption="Пример" />

        <button
          type="button"
          class="flex h-14 w-full items-center justify-center gap-2.5 rounded-full bg-primary font-label-lg text-label-lg font-bold text-on-primary shadow-lg shadow-primary/25 transition-all active:scale-[0.98]"
          @click="openClipRequest"
        >
          <MsIcon name="add_a_photo" :size="22" />
          Оживить фото героя
        </button>

        <section v-if="photo.data.value?.mine?.length" class="flex flex-col gap-space-sm">
          <h3 class="font-headline-sm text-headline-sm text-on-surface">Мои заявки</h3>
          <ClipCard
            v-for="clip in photo.data.value.mine"
            :key="clip.id"
            :clip="clip"
            :active="shownClip?.id === clip.id"
            :busy="busyClipId === clip.id"
            @watch="selectedClipId = clip.id"
            @retry="retry(clip)"
            @share="sheet = { kind: 'share', clip }"
          />
        </section>

        <section class="flex flex-col gap-space-sm">
          <h3 class="font-headline-sm text-headline-sm text-on-surface">Общий мемориал</h3>
          <div v-if="photo.data.value?.memorial.length" class="-mx-margin flex gap-space-sm overflow-x-auto px-margin pb-1">
            <button
              v-for="clip in photo.data.value.memorial"
              :key="clip.id"
              type="button"
              class="flex w-24 shrink-0 flex-col gap-1 text-left"
              @click="selectedClipId = clip.id"
            >
              <img :src="clip.source_photo_url" alt="" class="h-32 w-24 rounded-DEFAULT object-cover shadow-sm" />
              <span class="line-clamp-2 font-label-sm text-label-sm text-on-surface">{{ clip.soldier_name || 'Неизвестный боец' }}</span>
            </button>
          </div>
          <p v-else class="rounded-DEFAULT bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
            Здесь появятся ожившие портреты, которые семьи разрешили показать всем.
          </p>
        </section>
      </template>
    </template>

    <!-- Народный архив -->
    <template v-else-if="tab === 'archive'">
      <button
        type="button"
        class="flex h-12 w-full items-center justify-center gap-2 rounded-full bg-primary font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99]"
        @click="openPropose()"
      >
        <MsIcon name="edit_note" :size="22" />
        Предложить событие или героя
      </button>

      <div class="-mx-margin flex gap-space-xs overflow-x-auto px-margin pb-1">
        <button
          type="button"
          class="shrink-0 rounded-full px-3 py-1.5 font-label-md text-label-md"
          :class="kindFilter === null ? 'bg-secondary text-on-secondary' : 'bg-surface-container-low text-on-surface'"
          @click="kindFilter = null"
        >
          Все
        </button>
        <button
          v-for="(meta, value) in ENTRY_KINDS"
          :key="value"
          type="button"
          class="flex shrink-0 items-center gap-1 rounded-full px-3 py-1.5 font-label-md text-label-md"
          :class="kindFilter === value ? 'bg-secondary text-on-secondary' : 'bg-surface-container-low text-on-surface'"
          @click="kindFilter = value"
        >
          <MsIcon :name="meta.icon" :size="16" />
          {{ meta.title }}
        </button>
      </div>

      <StateBlock v-if="archive.loading.value || archive.error.value" :loading="archive.loading.value" :error="archive.error.value" @retry="archive.retry" />
      <template v-else>
        <section v-if="myEntries.length" class="flex flex-col gap-space-sm">
          <h3 class="font-headline-sm text-headline-sm text-on-surface">Мои записи</h3>
          <EntryCard v-for="entry in myEntries" :key="entry.id" :entry="entry" mine />
        </section>

        <section class="flex flex-col gap-space-sm">
          <h3 class="font-headline-sm text-headline-sm text-on-surface">Подтверждено краеведами</h3>
          <EntryCard v-for="entry in feed" :key="entry.id" :entry="entry" />
          <StateBlock
            v-if="!feed.length"
            :loading="false"
            :error="null"
            empty
            empty-icon="menu_book"
            empty-text="Подтверждённых записей пока нет — предложите первую"
          />
        </section>
      </template>
    </template>

    <!-- Проверка краеведом -->
    <template v-else-if="tab === 'review'">
      <InlineNotice icon="fact_check">
        Сверьте запись с Книгой Памяти Орловской области и сборником «Выстояли и победили!». Подтверждённая запись
        появится в общей ленте с отметкой «Подтверждено».
      </InlineNotice>
      <StateBlock v-if="queue.loading.value || queue.error.value" :loading="queue.loading.value" :error="queue.error.value" @retry="queue.retry" />
      <template v-else>
        <EntryCard
          v-for="entry in queue.data.value ?? []"
          :key="entry.id"
          :entry="entry"
          reviewable
          :busy="busyEntryId === entry.id"
          @review="(verdict, note) => review(entry, verdict, note)"
        />
        <StateBlock v-if="!queue.data.value?.length" :loading="false" :error="null" empty empty-icon="task_alt" empty-text="Все записи проверены" />
      </template>
    </template>

    <ClipRequestSheet v-if="sheet?.kind === 'clip'" @created="clipCreated" @close="sheet = null" />
    <ProposeEntrySheet v-else-if="sheet?.kind === 'propose'" :initial-kind="sheet.entryKind" @created="entryCreated" @close="sheet = null" />
    <ShareClipSheet v-else-if="sheet?.kind === 'share'" :clip="sheet.clip" @close="sheet = null" />
    <SheetDialog v-else-if="sheet?.kind === 'account'" title="Нужен аккаунт" @close="sheet = null">
      <AccountRequired :text="sheet.text" />
    </SheetDialog>
  </div>
</template>
