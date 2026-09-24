<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAsync } from '@/core/async'
import { errorText } from '@/core/format'
import type { LatLon } from '@/core/geo'
import { can, useSessionStore } from '@/core/session'
import AccountRequired from '@/ui/AccountRequired.vue'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SegmentTabs from '@/ui/SegmentTabs.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import StateBlock from '@/ui/StateBlock.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'

import ClipCard from './components/ClipCard.vue'
import ClipRequestSheet from './components/ClipRequestSheet.vue'
import EntryCard from './components/EntryCard.vue'
import HelpVerify from './components/HelpVerify.vue'
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
  deleteClip,
  deleteEntry,
  retryClip,
  reviewEntry,
  setClipPublic,
  type ArchiveEntry,
  type Clip,
  type EntryKind,
  type NearbyPending,
} from './data'

type Tab = 'photo' | 'archive' | 'review'
type Sheet =
  | { kind: 'clip' }
  | { kind: 'propose'; entryKind: EntryKind; about?: NearbyPending; entry?: ArchiveEntry }
  | { kind: 'share'; clip: Clip }
  | { kind: 'account'; text: string }

/**
 * Пример оформления, пока ни одного готового ролика нет: портрет из макета.
 * Подписан как пример — выдавать его за настоящего героя нельзя.
 */
const EXAMPLE_PORTRAIT =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuD2xyruqLOLailgDwisn_NnihcRFmdBlieraiQdmaqn0ppj6dkFlzXw6_Y7Y9K2rD4LRgGr9jB_ECv19-YEihit12h2WdRqODXXZE1czSNUvLTgTBbkRRzZ1i5Fm-3Poe33DEoMquYIhjDRZDedEY8deprL23qFYSthoaRgnLYbHYwjFMbG8uoeyFs-J7TLDluluY3_MUsv1VLoerDvDCfV-HfFNmiLSv5YZ19HHgFUY_1Ye3yNWfFK'

/** Как часто спрашивать статус заявок, пока хоть одна ждёт оживления, мс. */
const CLIP_POLL_MS = 15_000

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const canReview = computed(() => session.hasAccount && can.verifyArchive(session.user))

/** Вкладка — в адресе: из профиля «Добавить героя» ведёт сразу в архив с открытой формой. */
function tabFromQuery(): Tab {
  const tab = route.query.tab
  if (route.query.propose) return 'archive'
  return tab === 'archive' || (tab === 'review' && canReview.value) ? tab : 'photo'
}

const tab = ref<Tab>(tabFromQuery())
watch(tab, (value) => void router.replace({ query: { ...route.query, tab: value, propose: undefined } }))

/**
 * `?near=52.97,36.07` — точка, рядом с которой искать записи «на проверке».
 * Так карточка точки маршрута может позвать «помочь проверить» рядом с собой.
 */
const nearPoint = computed<LatLon | null>(() => {
  const [lat, lon] = String(route.query.near ?? '')
    .split(',')
    .map(Number)
  return Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? { lat, lon } : null
})

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

/** Убрать свой клип: он исчезнет и из семейного архива, и из общего мемориала. */
async function removeClip(clip: Clip): Promise<void> {
  if (busyClipId.value) return
  busyClipId.value = clip.id
  try {
    await deleteClip(clip.id)
    if (selectedClipId.value === clip.id) selectedClipId.value = null
    notice.value = { tone: 'success', text: `«${clip.soldier_name || 'Живое фото'}» убрано из архива` }
    await photo.retry()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    busyClipId.value = null
  }
}
const publishing = ref(false)

const myClips = computed(() => photo.data.value?.mine ?? [])
const memorial = computed(() => photo.data.value?.memorial ?? [])

/** Что показывает плеер: выбранный ролик, свой готовый, из мемориала — или пример. */
const shownClip = computed<Clip | null>(() => {
  const all = [...myClips.value, ...memorial.value].filter((clip) => clip.status === 'ready')
  return all.find((clip) => clip.id === selectedClipId.value) ?? all[0] ?? null
})
const shownIsMine = computed(() => !!shownClip.value && myClips.value.some((clip) => clip.id === shownClip.value?.id))

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

/**
 * Ожидание клипа: пока хоть одна заявка в очереди или оживляется, экран сам
 * спрашивает статус — готовое видео появится в плеере без «потяни, чтобы обновить».
 */
let clipPoll: ReturnType<typeof setInterval> | undefined
const waitingClips = computed(() => myClips.value.some((clip) => clip.status === 'queued' || clip.status === 'processing'))
watch(
  waitingClips,
  (waiting) => {
    clearInterval(clipPoll)
    clipPoll = waiting ? setInterval(() => void refreshPhoto(), CLIP_POLL_MS) : undefined
  },
  { immediate: true },
)
onBeforeUnmount(() => clearInterval(clipPoll))

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

async function togglePublic(clip: Clip, isPublic: boolean): Promise<void> {
  if (publishing.value) return
  publishing.value = true
  try {
    await setClipPublic(clip.id, isPublic)
    notice.value = {
      tone: 'success',
      text: isPublic ? 'Портрет появился в общем мемориале' : 'Портрет убран из мемориала — его видит только семья',
    }
    await refreshPhoto()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    publishing.value = false
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
const query = ref('')
const searching = ref(false)
const archive = useAsync(async () => {
  const [feed, mine] = await Promise.all([
    fetchPublicEntries(kindFilter.value, query.value),
    session.hasAccount ? fetchMyEntries() : Promise.resolve(null),
  ])
  return { feed, mine }
})

/**
 * Поиск и фильтр перечитывают ленту тихо, без спиннера на весь экран: человек
 * печатает, и список не должен мигать на каждую букву.
 */
let searchTimer: ReturnType<typeof setTimeout> | undefined
async function refreshFeed(): Promise<void> {
  searching.value = true
  try {
    const feed = await fetchPublicEntries(kindFilter.value, query.value)
    archive.data.value = { feed, mine: archive.data.value?.mine ?? null }
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    searching.value = false
  }
}
watch(kindFilter, () => void refreshFeed())
watch(query, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => void refreshFeed(), 350)
})
onBeforeUnmount(() => clearTimeout(searchTimer))

/** Свои записи — все стадии; в общей ленте — только подтверждённые, без повторов своих. */
const myEntries = computed(() =>
  (archive.data.value?.mine ?? []).filter((entry) => !kindFilter.value || entry.kind === kindFilter.value),
)
const feed = computed(() => {
  const mine = new Set(myEntries.value.map((entry) => entry.id))
  return (archive.data.value?.feed ?? []).filter((entry) => !mine.has(entry.id))
})

function openPropose(entryKind: EntryKind = 'event', about?: NearbyPending): void {
  sheet.value = session.hasAccount
    ? { kind: 'propose', entryKind, about }
    : { kind: 'account', text: about ? 'Помочь проверить запись можно с аккаунтом' : 'Предложить запись можно с аккаунтом' }
}

async function entryCreated(entry: ArchiveEntry): Promise<void> {
  const edited = sheet.value?.kind === 'propose' && sheet.value.entry !== undefined
  sheet.value = null
  tab.value = 'archive'
  notice.value = {
    tone: 'success',
    text: edited ? `«${entry.title}»: запись обновлена` : `«${entry.title}» отправлено краеведу на проверку`,
  }
  await archive.retry()
}

/** Убрать свою запись, пока она на проверке. */
async function removeEntry(entry: ArchiveEntry): Promise<void> {
  if (busyEntryId.value) return
  busyEntryId.value = entry.id
  try {
    await deleteEntry(entry.id)
    notice.value = { tone: 'success', text: `«${entry.title}»: запись убрана из архива` }
    await archive.retry()
  } catch (reason) {
    notice.value = { tone: 'error', text: errorText(reason) }
  } finally {
    busyEntryId.value = null
  }
}

// --- проверка краеведом ---

const queue = useAsync(async () => (canReview.value ? fetchModerationQueue() : []))
const busyEntryId = ref<string | null>(null)
const focusedEntryId = ref<string | null>(null)

/** Краевед нажал «Проверить» у записи рядом — ведём в очередь к этой записи. */
async function openReview(entryId: string): Promise<void> {
  tab.value = 'review'
  focusedEntryId.value = entryId
  await nextTick()
  document.getElementById(`memory-entry-${entryId}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  setTimeout(() => {
    if (focusedEntryId.value === entryId) focusedEntryId.value = null
  }, 2400)
}

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

const tabs = computed(() => [
  { value: 'photo' as const, title: 'Живое фото', icon: 'auto_awesome' },
  { value: 'archive' as const, title: 'Архив', icon: 'menu_book' },
  ...(canReview.value ? [{ value: 'review' as const, title: 'Проверка', icon: 'fact_check', count: queue.data.value?.length }] : []),
])
</script>

<template>
  <div class="flex w-full flex-col gap-space-md px-margin short:gap-space-sm">
    <header class="flex flex-col gap-space-xs">
      <p class="font-archival text-archival uppercase text-on-surface-variant">Память поколений · Орловщина</p>
      <h1
        class="ribbon-shimmer font-headline-lg text-headline-lg text-on-surface [--shimmer-base:theme(colors.ink.DEFAULT)] short:text-headline-lg-mobile"
      >
        Живая память
      </h1>
      <p class="font-body-sm text-body-sm text-on-surface-variant">Ожившие портреты героев и народный архив, который проверяют краеведы</p>
    </header>

    <SegmentTabs v-model="tab" :tabs="tabs" label="Разделы памяти" id-prefix="memory" />

    <InlineNotice v-if="notice" :tone="notice.tone">{{ notice.text }}</InlineNotice>

    <!-- Живое фото -->
    <section v-if="tab === 'photo'" id="memory-photo" role="tabpanel" aria-labelledby="memory-tab-photo" class="flex flex-col gap-space-md">
      <!-- Этическая оговорка кейса: без неё реконструкцию легко принять за подлинную запись. -->
      <div class="flex items-start gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
        <MsIcon name="shield_with_heart" :size="18" filled class="mt-0.5 shrink-0 text-secondary" />
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          Только в мемориальных целях, с уважением к памяти защитников Отечества. Движение и голос — реконструкция по
          архивной фотографии, а не подлинная запись.
        </p>
      </div>

      <StateBlock v-if="photo.loading.value || photo.error.value" :loading="photo.loading.value" :error="photo.error.value" @retry="photo.retry" />
      <template v-else>
        <div class="flex flex-col gap-space-sm">
          <LivingPortraitPlayer
            v-if="shownClip"
            :image="shownClip.source_photo_url"
            :video-url="shownClip.video_url"
            :line="shownClip.narration_text"
            :caption="shownClip.soldier_name || 'Живое фото'"
          />
          <LivingPortraitPlayer v-else :image="EXAMPLE_PORTRAIT" :line="DEFAULT_NARRATION" caption="Пример оформления" />

          <!-- Свой готовый портрет: сохранить в телефон, решить про мемориал, отправить родным. -->
          <div v-if="shownClip && shownIsMine" class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
            <div class="flex items-center justify-between gap-space-sm">
              <span class="min-w-0">
                <span class="block font-label-md text-label-md text-on-surface">В общем мемориале</span>
                <span class="block font-body-sm text-body-sm text-on-surface-variant">
                  {{ shownClip.is_public ? 'Портрет видят все' : 'Портрет хранится в семейном архиве' }}
                </span>
              </span>
              <ToggleSwitch
                :model-value="shownClip.is_public"
                label="Показать в общем мемориале"
                @update:model-value="(value) => shownClip && togglePublic(shownClip, value)"
              />
            </div>
            <div class="flex flex-wrap gap-space-xs">
              <button
                type="button"
                class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
                @click="sheet = { kind: 'share', clip: shownClip }"
              >
                <MsIcon name="send" :size="18" />
                Отправить родным
              </button>
              <a
                v-if="shownClip.video_url"
                :href="shownClip.video_url"
                target="_blank"
                rel="noopener"
                download
                class="flex items-center gap-space-xs rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
              >
                <MsIcon name="download" :size="18" />
                Сохранить видео
              </a>
            </div>
          </div>
          <p v-else-if="shownClip" class="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
            <MsIcon name="public" :size="15" />
            Из общего мемориала — семья разрешила показывать портрет всем
          </p>
          <p v-else class="flex items-center gap-space-xs font-body-sm text-body-sm text-on-surface-variant">
            <MsIcon name="info" :size="15" />
            Это пример — оживите фото своего героя, и здесь будет он
          </p>
        </div>

        <button
          type="button"
          class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
          @click="openClipRequest"
        >
          <MsIcon name="add_a_photo" :size="18" />
          <span>Оживить фото героя</span>
        </button>

        <section v-if="session.hasAccount" class="flex flex-col gap-space-sm">
          <div>
            <p class="font-archival text-archival uppercase text-on-surface-variant">Только для своих</p>
            <h2 class="font-headline-md text-headline-md text-on-surface">Семейный архив</h2>
          </div>
          <ClipCard
            v-for="clip in myClips"
            :key="clip.id"
            :clip="clip"
            :active="shownClip?.id === clip.id"
            :busy="busyClipId === clip.id"
            @watch="selectedClipId = clip.id"
            @retry="retry(clip)"
            @share="sheet = { kind: 'share', clip }"
            @remove="removeClip(clip)"
          />
          <p v-if="!myClips.length" class="rounded-2xl bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
            Здесь будут ожившие портреты вашей семьи. Их видите только вы — в мемориал портрет попадёт, если вы разрешите.
          </p>
        </section>

        <section class="flex flex-col gap-space-sm">
          <div>
            <p class="font-archival text-archival uppercase text-on-surface-variant">Открыто всем</p>
            <h2 class="font-headline-md text-headline-md text-on-surface">Общий мемориал</h2>
          </div>
          <div v-if="memorial.length" class="no-scrollbar -mx-margin flex gap-space-sm overflow-x-auto px-margin py-1">
            <button
              v-for="clip in memorial"
              :key="clip.id"
              type="button"
              class="flex w-24 shrink-0 flex-col gap-1 text-left active:scale-95"
              :aria-pressed="shownClip?.id === clip.id"
              @click="selectedClipId = clip.id"
            >
              <img
                :src="clip.source_photo_url"
                alt=""
                loading="lazy"
                class="h-32 w-24 rounded-2xl object-cover shadow-document transition-shadow duration-200"
                :class="{ 'ring-2 ring-secondary': shownClip?.id === clip.id }"
              />
              <span class="line-clamp-2 font-label-sm text-label-sm text-on-surface">{{ clip.soldier_name || 'Неизвестный боец' }}</span>
            </button>
          </div>
          <p v-else class="rounded-2xl bg-surface-container-low p-space-md font-body-sm text-body-sm text-on-surface-variant">
            Здесь появятся ожившие портреты, которые семьи разрешили показать всем.
          </p>
        </section>
      </template>
    </section>

    <!-- Народный архив -->
    <section v-else-if="tab === 'archive'" id="memory-archive" role="tabpanel" aria-labelledby="memory-tab-archive" class="flex flex-col gap-space-md">
      <button
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="openPropose()"
      >
        <MsIcon name="edit_note" :size="18" />
        <span>Предложить событие или героя</span>
      </button>

      <HelpVerify :point="nearPoint" :can-review="canReview" @help="(entry) => openPropose('memory', entry)" @review="openReview" />

      <div class="flex flex-col gap-space-sm">
        <label class="flex items-center gap-space-sm border-b border-outline-variant py-2 transition-colors focus-within:border-primary">
          <MsIcon :name="searching ? 'progress_activity' : 'search'" :size="18" class="text-on-surface-variant" :class="{ 'animate-spin': searching }" />
          <span class="sr-only">Поиск по архиву</span>
          <input
            v-model="query"
            type="search"
            placeholder="Фамилия, деревня, часть"
            class="w-full border-none bg-transparent font-body-md text-body-md text-on-surface outline-none placeholder:text-on-surface-variant focus-visible:ring-0"
          />
        </label>

        <div class="no-scrollbar -mx-margin flex gap-space-xs overflow-x-auto px-margin py-1" role="radiogroup" aria-label="Вид записи">
          <button
            type="button"
            role="radio"
            :aria-checked="kindFilter === null"
            class="shrink-0 rounded-full px-space-sm py-1.5 font-label-md text-label-md transition-colors duration-200 active:scale-95"
            :class="kindFilter === null ? 'bg-secondary text-on-secondary' : 'bg-surface-container-lowest text-on-surface-variant shadow-document'"
            @click="kindFilter = null"
          >
            Все
          </button>
          <button
            v-for="(meta, value) in ENTRY_KINDS"
            :key="value"
            type="button"
            role="radio"
            :aria-checked="kindFilter === value"
            class="flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full px-space-sm py-1.5 font-label-md text-label-md transition-colors duration-200 active:scale-95"
            :class="kindFilter === value ? 'bg-secondary text-on-secondary' : 'bg-surface-container-lowest text-on-surface-variant shadow-document'"
            @click="kindFilter = value"
          >
            <MsIcon :name="meta.icon" :size="15" />
            {{ meta.title }}
          </button>
        </div>
      </div>

      <StateBlock v-if="archive.loading.value || archive.error.value" :loading="archive.loading.value" :error="archive.error.value" @retry="archive.retry" />
      <template v-else>
        <div v-if="myEntries.length" class="flex flex-col gap-space-sm">
          <div>
            <p class="font-archival text-archival uppercase text-on-surface-variant">Вы предложили</p>
            <h2 class="font-headline-md text-headline-md text-on-surface">Мои записи</h2>
          </div>
          <EntryCard
            v-for="entry in myEntries"
            :key="entry.id"
            :entry="entry"
            mine
            :busy="busyEntryId === entry.id"
            @edit="sheet = { kind: 'propose', entryKind: entry.kind, entry }"
            @remove="removeEntry(entry)"
          />
        </div>

        <div class="flex flex-col gap-space-sm">
          <div>
            <p class="font-archival text-archival uppercase text-on-surface-variant">Лента архива</p>
            <h2 class="font-headline-md text-headline-md text-on-surface">Подтверждено краеведами</h2>
          </div>
          <EntryCard v-for="entry in feed" :key="entry.id" :entry="entry" />
          <StateBlock
            v-if="!feed.length"
            :loading="false"
            :error="null"
            empty
            :empty-icon="query ? 'search_off' : 'menu_book'"
            :empty-text="query ? 'По запросу ничего не нашлось' : 'Подтверждённых записей пока нет — предложите первую'"
          />
        </div>
      </template>
    </section>

    <!-- Проверка краеведом -->
    <section v-else-if="tab === 'review'" id="memory-review" role="tabpanel" aria-labelledby="memory-tab-review" class="flex flex-col gap-space-md">
      <InlineNotice icon="fact_check">
        Сверьте запись с Книгой Памяти Орловской области и сборником «Выстояли и победили!». Подтверждённая запись
        появится в общей ленте с отметкой «Подтверждено».
      </InlineNotice>
      <StateBlock v-if="queue.loading.value || queue.error.value" :loading="queue.loading.value" :error="queue.error.value" @retry="queue.retry" />
      <template v-else>
        <EntryCard
          v-for="entry in queue.data.value ?? []"
          :id="`memory-entry-${entry.id}`"
          :key="entry.id"
          :entry="entry"
          reviewable
          :busy="busyEntryId === entry.id"
          :focused="focusedEntryId === entry.id"
          @review="(verdict, note) => review(entry, verdict, note)"
        />
        <StateBlock v-if="!queue.data.value?.length" :loading="false" :error="null" empty empty-icon="task_alt" empty-text="Все записи проверены" />
      </template>
    </section>

    <ClipRequestSheet v-if="sheet?.kind === 'clip'" @created="clipCreated" @close="sheet = null" />
    <ProposeEntrySheet
      v-else-if="sheet?.kind === 'propose'"
      :initial-kind="sheet.entryKind"
      :about="sheet.about ?? null"
      :entry="sheet.entry ?? null"
      @created="entryCreated"
      @close="sheet = null"
    />
    <ShareClipSheet v-else-if="sheet?.kind === 'share'" :clip="sheet.clip" @close="sheet = null" />
    <SheetDialog v-else-if="sheet?.kind === 'account'" title="Нужен аккаунт" @close="sheet = null">
      <AccountRequired :text="sheet.text" />
    </SheetDialog>
  </div>
</template>
