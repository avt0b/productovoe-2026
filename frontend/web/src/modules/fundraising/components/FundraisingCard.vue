<script setup>
import SmartImage from '@shared/components/SmartImage.vue'

defineProps({
  emblemUrl: { type: String, default: '' },
  squadName: { type: String, default: 'Отряд «Высота»' },
  location: { type: String, default: 'г. Орёл' },
  tag: { type: String, default: 'Срочный сбор' },
  tagClass: { type: String, default: 'bg-surface-container-high text-on-surface-variant' },
  title: { type: String, default: 'Бензин для мотопомп и дизельный генератор' },
  text: {
    type: String,
    default:
      'Откачка грунтовых вод из заболоченных воронок у ручья Озерна. Без помпы невозможно поднять затопленный блиндаж.',
  },
  raised: { type: String, default: '35 000 ₽' },
  goal: { type: String, default: 'из 50 000 ₽' },
  percent: { type: Number, default: 70 },
  statusLabel: { type: String, default: 'Сбор открыт' },
  barClass: { type: String, default: 'bg-primary' },
  raisedTextClass: { type: String, default: 'text-primary' },
  ctaLabel: { type: String, default: 'Помочь отряду (от 100 ₽)' },
  ctaClass: { type: String, default: 'bg-primary hover:bg-primary/90 text-on-primary shadow-md' },
  ctaIcon: { type: String, default: 'volunteer_activism' },
  ctaIconClass: { type: String, default: '' },
})

defineEmits(['donate'])
</script>

<template>
  <div class="bg-surface-container-lowest rounded-lg p-6 shadow-sm flex flex-col justify-between relative group hover:shadow-md transition-all">
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center text-primary font-bold overflow-hidden shrink-0">
            <SmartImage :src="emblemUrl" icon="shield" img-class="w-full h-full object-cover" />
          </div>
          <div>
            <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold group-hover:text-primary transition-colors">
              {{ squadName }}
            </h3>
            <span class="font-label-sm text-label-sm text-outline flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">pin_drop</span>
              {{ location }}
            </span>
          </div>
        </div>
        <span class="px-2.5 py-1 rounded-full font-label-sm text-label-sm font-semibold" :class="tagClass">
          {{ tag }}
        </span>
      </div>

      <div class="flex flex-col gap-1.5">
        <h4 class="font-label-lg text-label-lg text-on-surface font-bold leading-snug">{{ title }}</h4>
        <p class="font-body-sm text-body-sm text-on-surface-variant line-clamp-2">{{ text }}</p>
      </div>

      <div class="flex flex-col gap-2 pt-2">
        <div class="flex justify-between items-baseline">
          <span class="font-headline-sm text-headline-sm font-bold" :class="raisedTextClass">{{ raised }}</span>
          <span class="font-body-sm text-body-sm text-outline">{{ goal }}</span>
        </div>
        <div class="w-full h-2.5 bg-surface-container-high rounded-full overflow-hidden">
          <div class="h-full rounded-full transition-all duration-500" :class="barClass" :style="{ width: percent + '%' }" />
        </div>
        <div class="flex justify-between items-center text-label-sm font-label-sm text-outline pt-0.5">
          <span class="flex items-center gap-1">
            <span class="material-symbols-outlined text-[15px] text-tertiary">favorite</span>
            {{ statusLabel }}
          </span>
          <span class="font-bold text-on-surface">{{ percent }}% собрано</span>
        </div>
      </div>
    </div>

    <div class="pt-6 mt-4">
      <button
        class="w-full py-3.5 px-6 rounded-full font-label-lg text-label-lg font-bold hover:scale-[0.99] transition-all flex items-center justify-center gap-2"
        :class="ctaClass"
        @click="$emit('donate')"
      >
        <span class="material-symbols-outlined text-[20px]" :class="ctaIconClass">{{ ctaIcon }}</span>
        <span>{{ ctaLabel }}</span>
      </button>
    </div>
  </div>
</template>
