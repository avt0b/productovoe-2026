<script setup>
defineProps({
  userName: { type: String, default: 'Михаил Смирнов' },
  userRole: { type: String, default: 'Командир поискового отряда' },
  liveStatus: { type: String, default: 'Орловский плацдарм в эфире' },
  sidebarOpen: { type: Boolean, default: true },
})
defineEmits(['toggle-sidebar'])
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 h-16 bg-surface/85 backdrop-blur-xl shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-30 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-3 transition-[left] duration-300 ease-out"
    :class="sidebarOpen ? 'lg:left-72' : 'lg:left-0'"
  >
    <div class="flex items-center gap-2 sm:gap-4 flex-1 min-w-0">
      <button
        class="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors shrink-0"
        title="Показать/скрыть боковую панель"
        @click="$emit('toggle-sidebar')"
      >
        <span class="material-symbols-outlined text-[22px]">{{ sidebarOpen ? 'menu_open' : 'menu' }}</span>
      </button>

      <div class="relative w-full max-w-xl hidden sm:block">
        <span class="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant text-[20px]">
          search
        </span>
        <input
          type="search"
          placeholder="Поиск по мемориалам, дивизиям, картам и бойцам..."
          class="w-full h-10 pl-10 pr-4 bg-surface-container-low rounded-full font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant outline-none focus:bg-surface-container-lowest transition-colors"
        />
      </div>
    </div>

    <div class="flex items-center gap-2 sm:gap-4 shrink-0">
      <div class="hidden xl:flex items-center gap-2 bg-secondary-fixed text-on-secondary-fixed px-3 py-1.5 rounded-full">
        <span class="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
        <span class="font-label-sm text-label-sm font-bold">{{ liveStatus }}</span>
      </div>
      <button
        class="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors shrink-0"
      >
        <span class="material-symbols-outlined text-[22px]">notifications</span>
      </button>
      <div class="flex items-center gap-3 pl-0 sm:pl-2">
        <div class="flex-col text-right hidden sm:flex">
          <span class="font-label-md text-label-md text-on-surface font-bold leading-tight">{{ userName }}</span>
          <span class="font-label-sm text-label-sm text-secondary">{{ userRole }}</span>
        </div>
        <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined text-on-primary text-[18px]">person</span>
        </div>
      </div>
    </div>
  </header>
</template>
