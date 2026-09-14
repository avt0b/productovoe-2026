<script setup>
import SmartImage from '@shared/components/SmartImage.vue'

defineProps({
  name: { type: String, default: 'Константин Смирнов' },
  role: { type: String, default: 'Поисковик-исследователь' },
  id: { type: String, default: '#МР-84920' },
  years: { type: String, default: '3 года' },
  squad: { type: String, default: 'Отряд «Высота», г. Орёл' },
  avatarUrl: { type: String, default: 'https://loremflickr.com/200/200/man,portrait,outdoor?lock=101' },
  rank: { type: String, default: 'Полевой следопыт III степени' },
  rankProgress: { type: Number, default: 80 },
  rankNext: { type: String, default: 'Полевой следопыт II степени' },
  rankPointsLeft: { type: Number, default: 250 },
})
</script>

<template>
  <section class="relative rounded-lg overflow-hidden bg-secondary text-on-secondary shadow-md p-8 mb-8">
    <div class="absolute -right-24 -top-24 w-96 h-96 rounded-full bg-secondary-fixed/10 blur-3xl pointer-events-none" />
    <div class="absolute right-1/4 -bottom-20 w-80 h-80 rounded-full bg-primary/10 blur-2xl pointer-events-none" />

    <div class="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-8">
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-6">
        <div class="relative shrink-0">
          <div
            class="w-24 h-24 rounded-full overflow-hidden shadow-md ring-4 ring-secondary-fixed/30 bg-surface-container-high"
          >
            <SmartImage :src="avatarUrl" icon="person" img-class="w-full h-full object-cover" />
          </div>
          <div
            class="absolute -bottom-1 -right-1 bg-secondary-container text-on-secondary-container p-1 rounded-full shadow-sm flex items-center justify-center"
            title="Верифицированный поисковик"
          >
            <span class="material-symbols-outlined text-[18px]" style="font-variation-settings: 'FILL' 1">verified</span>
          </div>
        </div>

        <div class="flex flex-col">
          <div class="flex flex-wrap items-center gap-2.5 mb-1.5">
            <h1 class="font-headline-lg text-headline-lg text-on-secondary font-bold">{{ name }}</h1>
            <span
              class="bg-secondary-fixed/20 text-secondary-fixed px-3 py-0.5 rounded-full font-label-sm text-label-sm uppercase font-bold tracking-wide"
            >
              {{ role }}
            </span>
          </div>
          <p class="font-body-md text-body-md text-secondary-fixed-dim mb-3">
            ID: <span class="font-bold text-on-secondary">{{ id }}</span> • Стаж {{ years }} • {{ squad }}
          </p>
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-1.5 bg-secondary-fixed/15 px-3 py-1 rounded-full font-label-md text-label-md">
              <span class="material-symbols-outlined text-[16px] text-tertiary-fixed">military_tech</span>
              <span class="text-on-secondary font-semibold">Вахта Памяти 2024</span>
            </div>
            <div class="flex items-center gap-1.5 bg-secondary-fixed/15 px-3 py-1 rounded-full font-label-md text-label-md">
              <span class="material-symbols-outlined text-[16px] text-secondary-fixed">qr_code_2</span>
              <span class="text-on-secondary font-semibold">Полевой жетон: Активен</span>
            </div>
          </div>
        </div>
      </div>

      <div
        class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 bg-on-secondary-fixed/30 p-4 rounded-DEFAULT backdrop-blur-md self-stretch xl:self-auto"
      >
        <div class="flex items-center gap-3 pr-4">
          <div class="w-12 h-12 rounded-lg bg-surface-container-lowest p-1.5 flex items-center justify-center shrink-0 shadow-sm">
            <span class="material-symbols-outlined text-on-surface text-[28px]">qr_code_2</span>
          </div>
          <div class="flex flex-col">
            <span class="font-label-sm text-label-sm text-secondary-fixed-dim uppercase">Пропуск в полевые архивы</span>
            <span class="font-label-md text-label-md font-bold text-on-secondary">ЦАМО / Орловский сектор</span>
          </div>
        </div>
        <button
          class="bg-primary hover:bg-primary-container text-on-primary font-label-md text-label-md font-bold px-5 py-3 rounded-full transition-all shadow-sm flex items-center justify-center gap-2"
        >
          <span class="material-symbols-outlined text-[18px]">download</span>
          <span>Экспорт жетона</span>
        </button>
      </div>
    </div>

    <div class="mt-8 pt-6 bg-on-secondary-fixed/20 -mx-8 -mb-8 px-8 py-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
        <div class="flex items-center gap-2">
          <span class="font-label-md text-label-md font-bold text-secondary-fixed">Текущий ранг:</span>
          <span class="font-label-md text-label-md text-on-secondary">{{ rank }}</span>
        </div>
        <span class="font-label-sm text-label-sm text-tertiary-fixed font-bold tracking-wider uppercase">
          {{ rankProgress }}% до «{{ rankNext }}» (еще {{ rankPointsLeft }} очков)
        </span>
      </div>
      <div class="w-full h-3 bg-secondary-fixed/20 rounded-full overflow-hidden p-0.5">
        <div
          class="h-full bg-gradient-to-r from-tertiary-fixed-dim via-tertiary to-primary rounded-full transition-all duration-500"
          :style="{ width: rankProgress + '%' }"
        />
      </div>
    </div>
  </section>
</template>
