<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import { ORGANIZATION_KINDS, organizationKind, type OrganizationKind } from '@/core/services/organizations'
import { can, useSessionStore } from '@/core/session'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { createSquad, deleteSquad, updateSquad, type Squad } from '../data'

/**
 * Отряд, музей или школа: заводит поисковик (музей и школу — ещё и краевед),
 * ведёт — командир. Это же окно правит уже заведённую организацию и
 * распускает её: сборы и выезды уходят вместе с ней, поэтому роспуск — в два
 * нажатия.
 */
const props = withDefaults(defineProps<{ squad?: Squad | null }>(), { squad: null })

const emit = defineEmits<{ close: []; created: [squad: Squad]; removed: [squad: Squad] }>()

const session = useSessionStore()

const KINDS: readonly { kind: OrganizationKind; hint: string; placeholder: string; save: string; remove: string }[] = [
  {
    kind: 'squad',
    hint: 'Раскопки, Вахты Памяти, подъём бойцов',
    placeholder: 'Поисковый отряд «Высота»',
    save: 'Создать отряд',
    remove: 'Распустить отряд',
  },
  {
    kind: 'museum',
    hint: 'Экспозиции, фонды, работа с архивом',
    placeholder: 'Орловский военно-исторический музей',
    save: 'Добавить музей',
    remove: 'Удалить музей',
  },
  {
    kind: 'school',
    hint: 'Поисковый или краеведческий клуб',
    placeholder: 'Поисковый клуб «Память» при школе № 26',
    save: 'Добавить школу',
    remove: 'Удалить школу',
  },
]

/** Поисковый отряд заводит только поисковик: краеведу эта карточка недоступна. */
function kindAllowed(kind: OrganizationKind): boolean {
  if (props.squad) return true
  return kind === 'squad' ? can.createSquad(session.user) : can.createOrganization(session.user)
}

const kind = ref<OrganizationKind>(
  props.squad ? organizationKind(props.squad.kind) : (KINDS.find((item) => kindAllowed(item.kind))?.kind ?? 'squad'),
)
const name = ref(props.squad?.name ?? '')
// Новую организацию чаще заводят в своём городе — подставляем его из профиля.
const region = ref(props.squad?.region ?? session.user?.city ?? '')
const description = ref(props.squad?.description ?? '')
const contact = ref(props.squad?.contact ?? '')
const saving = ref(false)
const confirmingDelete = ref(false)
const error = ref<string | null>(null)
const tried = ref(false)

const look = computed(() => KINDS.find((item) => item.kind === kind.value) ?? KINDS[0])
const missing = computed(() => {
  if (!name.value.trim()) return 'Как называется?'
  if (!region.value.trim()) return 'В каком городе? По нему организацию найдут в заявках и на карте'
  return null
})
const shownError = computed(() => error.value ?? (tried.value ? missing.value : null))

async function submit(): Promise<void> {
  if (saving.value) return
  if (missing.value) {
    tried.value = true
    return
  }
  saving.value = true
  error.value = null
  const draft = {
    name: name.value.trim(),
    kind: kind.value,
    region: region.value.trim(),
    description: description.value.trim(),
    contact: contact.value.trim(),
  }
  try {
    emit('created', props.squad ? await updateSquad(props.squad.id, draft) : await createSquad(draft))
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

async function disband(): Promise<void> {
  const squad = props.squad
  if (!squad || saving.value) return
  saving.value = true
  error.value = null
  try {
    await deleteSquad(squad.id)
    emit('removed', squad)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog
    :title="squad ? 'Сведения об организации' : 'Новая организация'"
    :subtitle="squad ? 'Правит командир — их видят волонтёры и все, кто подаёт заявку на роль' : 'Вы станете её командиром'"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-lg" novalidate @submit.prevent="submit">
      <!-- Как организацию увидят в «Штабе» и в заявках — меняется вместе с графами. -->
      <div class="flex items-center gap-space-sm rounded-2xl bg-surface-container-low p-space-md">
        <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-secondary text-on-secondary" aria-hidden="true">
          <MsIcon :name="ORGANIZATION_KINDS[kind].icon" :size="24" />
        </span>
        <div class="min-w-0">
          <p class="font-archival text-archival uppercase text-on-surface-variant">{{ ORGANIZATION_KINDS[kind].title }}</p>
          <p class="truncate font-headline-sm text-headline-sm" :class="name.trim() ? 'text-on-surface' : 'text-outline'">
            {{ name.trim() || look.placeholder }}
          </p>
          <p class="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
            <MsIcon name="location_on" :size="15" class="shrink-0 text-secondary" />
            {{ region.trim() || 'Город не указан' }}
          </p>
        </div>
      </div>

      <section class="flex flex-col gap-space-sm">
        <p class="font-archival text-archival uppercase text-on-surface-variant">Кто вы</p>
        <div class="grid grid-cols-3 gap-space-xs" role="radiogroup" aria-label="Вид организации">
          <button
            v-for="item in KINDS"
            :key="item.kind"
            type="button"
            role="radio"
            :aria-checked="kind === item.kind"
            :disabled="!kindAllowed(item.kind)"
            class="flex flex-col items-center gap-1 rounded-2xl border p-space-sm text-center transition-colors duration-200 active:scale-95 disabled:opacity-40"
            :class="kind === item.kind ? 'border-secondary bg-secondary-container/70' : 'border-outline-variant/60 bg-surface-container-lowest'"
            @click="kind = item.kind"
          >
            <MsIcon :name="ORGANIZATION_KINDS[item.kind].icon" :size="22" :class="kind === item.kind ? 'text-secondary' : 'text-on-surface-variant'" />
            <span class="font-label-md text-label-md text-on-surface">{{ ORGANIZATION_KINDS[item.kind].title }}</span>
          </button>
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant">
          {{ kindAllowed('squad') || squad ? look.hint : `${look.hint}. Поисковый отряд заводит поисковик.` }}
        </p>
      </section>

      <section class="flex flex-col gap-space-md">
        <p class="font-archival text-archival uppercase text-on-surface-variant">О вас</p>
        <FormInput v-model="name" label="Название" icon="badge" :maxlength="200" :placeholder="look.placeholder" />
        <FormInput
          v-model="region"
          label="Город"
          icon="location_on"
          :maxlength="120"
          placeholder="Орёл"
          hint="По городу вас найдут в заявках на роль и на карте потребностей"
        />
        <FormTextarea v-model="description" label="Чем занимаетесь" placeholder="Какие рубежи, экспедиции, экспозиции, с кем работаете" />
      </section>

      <section class="flex flex-col gap-space-md">
        <p class="font-archival text-archival uppercase text-on-surface-variant">Для связи</p>
        <FormInput v-model="contact" label="Как связаться" icon="call" :maxlength="300" placeholder="Телефон штаба или ссылка на чат" />
      </section>

      <div class="flex flex-col gap-space-sm">
        <InlineNotice v-if="shownError" tone="error">{{ shownError }}</InlineNotice>
        <button
          type="submit"
          class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
          :disabled="saving"
        >
          <MsIcon :name="saving ? 'progress_activity' : ORGANIZATION_KINDS[kind].icon" :size="18" :class="{ 'animate-spin': saving }" />
          <span>{{ squad ? 'Сохранить' : look.save }}</span>
        </button>
      </div>

      <!-- Роспуск — в два нажатия: вместе с организацией уходят её сборы, выезды и их переписка. -->
      <template v-if="squad">
        <button
          type="button"
          class="-mt-space-sm flex items-center gap-space-xs self-center rounded-full px-space-md py-2 font-label-md text-label-md text-error active:scale-95"
          :aria-expanded="confirmingDelete"
          @click="confirmingDelete = !confirmingDelete"
        >
          <MsIcon name="delete" :size="18" />
          {{ look.remove }}
        </button>
        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="confirmingDelete ? 'grid-rows-[1fr] opacity-100' : '-mt-space-lg grid-rows-[0fr] opacity-0'"
          :inert="!confirmingDelete"
        >
          <div class="overflow-hidden">
            <div class="flex flex-col gap-space-sm rounded-2xl bg-error-container p-space-md" role="alertdialog" aria-label="Подтверждение удаления">
              <p class="font-body-sm text-body-sm text-on-error-container">
                Вместе с «{{ squad.name }}» уйдут все её сборы, выезды и переписка в них. Это не отменить.
              </p>
              <div class="flex gap-space-sm">
                <button
                  type="button"
                  class="flex-1 rounded-full bg-surface-container-lowest py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
                  @click="confirmingDelete = false"
                >
                  Оставить
                </button>
                <button
                  type="button"
                  class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error active:scale-95 disabled:opacity-60"
                  :disabled="saving"
                  @click="disband"
                >
                  <MsIcon name="delete" :size="18" />
                  Удалить
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </form>
  </SheetDialog>
</template>
