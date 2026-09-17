<script setup>
const actions = [
  {
    icon: 'folder_shared',
    bg: 'bg-primary-fixed',
    fg: 'text-on-primary-fixed',
    hoverBg: 'group-hover:bg-primary',
    hoverFg: 'group-hover:text-on-primary',
    accent: 'text-primary',
    title: 'Сохранить в семейный архив',
    text: 'Папка «Герои семьи Вороновых» (облачная синхронизация)',
    cta: 'Добавить ветку',
    ctaIcon: 'add_circle',
  },
  {
    icon: 'map',
    bg: 'bg-secondary-fixed',
    fg: 'text-on-secondary-fixed',
    hoverBg: 'group-hover:bg-secondary',
    hoverFg: 'group-hover:text-on-secondary',
    accent: 'text-secondary',
    title: 'На карту мемориала',
    text: 'Координаты рубежа 1941–1942: 53°31\'12"N 36°14\'45"E',
    cta: 'Маршрут памяти',
    ctaIcon: 'place',
  },
  {
    icon: 'qr_code_2',
    bg: 'bg-tertiary-fixed',
    fg: 'text-on-tertiary-fixed',
    hoverBg: 'group-hover:bg-tertiary',
    hoverFg: 'group-hover:text-on-tertiary',
    accent: 'text-tertiary',
    title: 'Поделиться историей',
    text: 'Создать интерактивный QR для семейного фотоальбома',
    cta: 'Создать код',
    ctaIcon: 'share',
  },
]
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div
      v-for="action in actions"
      :key="action.title"
      class="bg-surface-container-lowest rounded-DEFAULT p-4 shadow-sm hover:shadow-md transition-all flex flex-col justify-between group cursor-pointer"
    >
      <div class="flex flex-col gap-2">
        <div
          class="w-10 h-10 rounded-full flex items-center justify-center transition-colors"
          :class="[action.bg, action.fg, action.hoverBg, action.hoverFg]"
        >
          <span class="material-symbols-outlined text-[20px]">{{ action.icon }}</span>
        </div>
        <span class="font-label-md text-label-md text-on-surface font-bold leading-tight">{{ action.title }}</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ action.text }}</span>
      </div>
      <div class="mt-4 pt-3 flex items-center justify-between font-label-sm text-label-sm font-bold" :class="action.accent">
        <span>{{ action.cta }}</span>
        <span class="material-symbols-outlined text-[16px] group-hover:translate-x-1 transition-transform">
          {{ action.ctaIcon }}
        </span>
      </div>
    </div>
  </div>
</template>
