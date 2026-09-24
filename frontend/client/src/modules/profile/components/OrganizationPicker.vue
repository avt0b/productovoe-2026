<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { ORGANIZATION_KINDS, organizationKind, sameCity, type OrganizationKind } from '@/core/services/organizations'
import MsIcon from '@/ui/MsIcon.vue'
import FormInput from '@/ui/form/FormInput.vue'
import { FIELD_HINT_CLASS, FIELD_LABEL_CLASS } from '@/ui/form/styles'

import type { SquadOption } from '../data'

/**
 * К какой организации человек себя относит: отряд, музей или школа его города.
 * Список — из «Штаба»; город — из профиля. Своей организации в списке нет —
 * можно вписать название: администратор разберётся, а отряд заведут потом.
 */
const props = defineProps<{
  organizations: SquadOption[]
  city: string
  /** Какие виды показывать первыми: поисковику — отряды, краеведу — музеи. */
  order: readonly OrganizationKind[]
}>()

/** id выбранной организации, `other` — вписали свою, `null` — не выбрано. */
const selected = defineModel<string | null>({ required: true })
const otherName = defineModel<string>('otherName', { required: true })

const kindFilter = ref<OrganizationKind | 'all'>('all')

const inCity = computed(() => props.organizations.filter((item) => item.region && sameCity(item.region, props.city)))
/** Города нет в профиле или в нём пока никого — показываем всех, а не пустоту. */
const pool = computed(() => (props.city.trim() && inCity.value.length ? inCity.value : props.organizations))
const scope = computed(() => {
  if (!props.city.trim()) return 'Город в профиле не указан — показываем организации всех городов.'
  if (!inCity.value.length) return `В городе «${props.city}» пока никого нет — показываем другие города.`
  return `Организации города «${props.city}».`
})

const sorted = computed(() =>
  [...pool.value].sort(
    (a, b) =>
      props.order.indexOf(organizationKind(a.kind)) - props.order.indexOf(organizationKind(b.kind)) ||
      a.name.localeCompare(b.name, 'ru'),
  ),
)
const kinds = computed(() => props.order.filter((kind) => sorted.value.some((item) => organizationKind(item.kind) === kind)))
const visible = computed(() =>
  kindFilter.value === 'all' ? sorted.value : sorted.value.filter((item) => organizationKind(item.kind) === kindFilter.value),
)

watch(
  () => props.city,
  () => (kindFilter.value = 'all'),
)

function pick(id: string): void {
  selected.value = selected.value === id ? null : id
}
</script>

<template>
  <fieldset class="flex flex-col gap-space-sm">
    <legend :class="FIELD_LABEL_CLASS">Отряд, музей или школа</legend>
    <p :class="FIELD_HINT_CLASS">{{ scope }} Город меняется в настройках профиля.</p>

    <div v-if="kinds.length > 1" class="no-scrollbar -mx-1 flex gap-space-xs overflow-x-auto px-1 py-0.5" role="radiogroup" aria-label="Вид организации">
      <button
        v-for="option in [{ value: 'all' as const, title: 'Все', icon: 'apps' }, ...kinds.map((kind) => ({ value: kind, title: ORGANIZATION_KINDS[kind].many, icon: ORGANIZATION_KINDS[kind].icon }))]"
        :key="option.value"
        type="button"
        role="radio"
        :aria-checked="kindFilter === option.value"
        class="flex shrink-0 items-center gap-1 rounded-full px-space-sm py-1.5 font-label-md text-label-md transition-colors duration-200 active:scale-95"
        :class="kindFilter === option.value ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-on-surface-variant'"
        @click="kindFilter = option.value"
      >
        <MsIcon :name="option.icon" :size="15" />
        {{ option.title }}
      </button>
    </div>

    <ul v-if="visible.length" class="flex max-h-64 flex-col gap-space-xs overflow-y-auto overscroll-contain pr-0.5" role="radiogroup" aria-label="Организация">
      <li v-for="item in visible" :key="item.id">
        <button
          type="button"
          role="radio"
          :aria-checked="selected === item.id"
          class="flex w-full items-center gap-space-sm rounded-2xl border p-space-sm text-left transition-colors duration-200 active:scale-[0.99]"
          :class="selected === item.id ? 'border-secondary bg-secondary-container/70' : 'border-outline-variant/60 bg-surface-container-lowest'"
          @click="pick(item.id)"
        >
          <span
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
            :class="selected === item.id ? 'bg-secondary text-on-secondary' : 'bg-surface-container-high text-secondary'"
            aria-hidden="true"
          >
            <MsIcon :name="ORGANIZATION_KINDS[organizationKind(item.kind)].icon" :size="20" />
          </span>
          <span class="flex min-w-0 flex-1 flex-col">
            <span class="font-label-lg text-label-lg text-on-surface">{{ item.name }}</span>
            <span class="font-body-sm text-body-sm text-on-surface-variant">
              {{ ORGANIZATION_KINDS[organizationKind(item.kind)].title }}{{ item.region ? ` · ${item.region}` : '' }}
            </span>
          </span>
          <MsIcon v-if="selected === item.id" name="check_circle" :size="20" filled class="shrink-0 text-secondary" />
        </button>
      </li>
    </ul>
    <p v-else class="rounded-2xl bg-surface-container-low p-space-sm text-center font-body-sm text-body-sm text-on-surface-variant">
      Организаций пока нет — впишите свою ниже.
    </p>

    <button
      type="button"
      role="radio"
      :aria-checked="selected === 'other'"
      class="flex items-center gap-space-xs self-start rounded-full px-space-md py-2 font-label-md text-label-md transition-colors duration-200 active:scale-95"
      :class="selected === 'other' ? 'bg-secondary-container text-on-secondary-container' : 'bg-surface-container-high text-on-surface'"
      @click="pick('other')"
    >
      <MsIcon :name="selected === 'other' ? 'check' : 'add'" :size="18" />
      Моей организации нет в списке
    </button>
    <div
      class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
      :class="selected === 'other' ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
      :inert="selected !== 'other'"
    >
      <div class="overflow-hidden">
        <FormInput v-model="otherName" label="Название" icon="edit" :maxlength="200" placeholder="Поисковый отряд «Высота», Орёл" />
      </div>
    </div>
  </fieldset>
</template>
