<script setup>
import { computed } from 'vue'
import SmartImage from '@shared/components/SmartImage.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  hero: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'edit'])

// Те же статусы судьбы, что и в компактном чипе списка, но со своим
// оформлением — эта карточка читается как архивное личное дело.
const STATUS_META = {
  killed_in_action: { label: 'Погиб в бою', icon: 'star', class: 'bg-primary text-on-primary' },
  missing_in_action: { label: 'Пропал без вести', icon: 'help', class: 'bg-tertiary text-on-tertiary' },
  died_of_wounds: { label: 'Умер от ран', icon: 'local_hospital', class: 'bg-error text-on-error' },
  veteran: { label: 'Дожил до Победы', icon: 'military_tech', class: 'bg-secondary text-on-secondary' },
}

const meta = computed(() => STATUS_META[props.hero?.status] ?? { label: props.hero?.status, icon: 'person', class: 'bg-outline text-surface' })

const yearsLabel = computed(() => {
  const h = props.hero
  if (!h) return ''
  if (!h.birth_year && !h.death_year) return ''
  return `${h.birth_year ?? '?'} — ${h.death_year ?? '?'}`
})

const lifespan = computed(() => {
  const h = props.hero
  if (h?.birth_year && h?.death_year) return `${h.death_year - h.birth_year} лет`
  return ''
})

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <div
    v-if="modelValue && hero"
    class="fixed inset-0 z-50 bg-night/60 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="relative bg-surface-container-lowest rounded-2xl max-w-lg w-full shadow-sheet overflow-hidden max-h-[92vh] flex flex-col">
      <!-- Печать-уголок: декоративный акцент архивного дела -->
      <div
        class="absolute top-4 right-4 z-10 w-11 h-11 rounded-full bg-ribbon-orange-pale text-ribbon-orange-deep flex items-center justify-center shadow-stamp rotate-6"
      >
        <span class="material-symbols-outlined text-[20px]" style="font-variation-settings: 'FILL' 1">military_tech</span>
      </div>

      <button
        class="absolute top-4 left-4 z-10 w-9 h-9 rounded-full bg-surface-container-lowest/90 backdrop-blur hover:bg-surface-container text-on-surface flex items-center justify-center shadow-float transition-colors"
        @click="close"
      >
        <span class="material-symbols-outlined text-[18px]">close</span>
      </button>

      <div class="overflow-y-auto flex flex-col">
        <!-- Портрет: во всю ширину, тёплая подложка вместо серого плейсхолдера -->
        <div class="relative h-64 shrink-0 bg-gradient-to-b from-parchment-shade to-parchment-dim">
          <SmartImage :src="hero.photo_url" icon="portrait" img-class="w-full h-full object-cover" />
          <div class="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-ink/70 to-transparent pointer-events-none" />
          <div class="absolute bottom-4 left-5 right-5 flex items-end justify-between gap-3">
            <div class="flex flex-col min-w-0">
              <span class="font-archival text-archival uppercase text-parchment-lightest/80">Герой семьи</span>
              <h1 class="font-headline-lg text-headline-lg text-parchment-lightest font-bold [overflow-wrap:anywhere]">
                {{ hero.name }}
              </h1>
            </div>
          </div>
        </div>

        <div class="p-6 flex flex-col gap-5">
          <div class="flex items-center gap-2.5 flex-wrap">
            <span class="px-3 py-1.5 rounded-full font-label-md text-label-md font-bold flex items-center gap-1.5" :class="meta.class">
              <span class="material-symbols-outlined text-[16px]" style="font-variation-settings: 'FILL' 1">{{ meta.icon }}</span>
              {{ meta.label }}
            </span>
            <span v-if="yearsLabel" class="font-label-md text-label-md text-on-surface-variant">{{ yearsLabel }}</span>
            <span v-if="lifespan" class="font-label-sm text-label-sm text-on-surface-variant">({{ lifespan }})</span>
          </div>

          <div v-if="hero.unit" class="flex items-start gap-3">
            <span class="material-symbols-outlined text-[20px] text-secondary shrink-0 mt-0.5">shield</span>
            <div class="flex flex-col">
              <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Часть</span>
              <span class="font-body-md text-body-md text-on-surface">{{ hero.unit }}</span>
            </div>
          </div>

          <div v-if="hero.note" class="relative bg-parchment-lighter rounded-DEFAULT p-4 shadow-document">
            <span class="material-symbols-outlined absolute top-3 right-3 text-[22px] text-parchment-line">format_quote</span>
            <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold block mb-1">Заметка</span>
            <p class="font-body-md text-body-md text-ink [overflow-wrap:anywhere]">{{ hero.note }}</p>
          </div>

          <p class="font-archival text-archival uppercase text-on-surface-variant text-center pt-2">
            Сохраняя подвиг защитников Отечества для будущих поколений
          </p>
        </div>
      </div>

      <div class="p-5 border-t border-surface-container-high shrink-0 flex justify-end">
        <button
          type="button"
          class="px-6 py-2.5 rounded-full bg-primary text-on-primary font-label-md text-label-md font-bold shadow-sm flex items-center gap-2"
          @click="$emit('edit', hero)"
        >
          <span class="material-symbols-outlined text-[18px]">edit</span>
          Изменить
        </button>
      </div>
    </div>
  </div>
</template>
