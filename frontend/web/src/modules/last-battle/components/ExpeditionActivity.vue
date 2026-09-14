<script setup>
defineProps({
  squadName: { type: String, default: 'Поисковый отряд «Костёр»' },
  role: { type: String, default: 'Курирует протокол эксгумации' },
  actNumber: { type: String, default: 'Акт № 41/8' },
})

const members = [
  { initials: 'МС', bg: 'bg-primary', fg: 'text-on-primary' },
  { initials: 'АК', bg: 'bg-secondary', fg: 'text-on-secondary' },
  { initials: 'ЕЛ', bg: 'bg-tertiary', fg: 'text-on-tertiary' },
]
</script>

<template>
  <div class="p-3 bg-surface-container-low rounded-DEFAULT flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="flex -space-x-2">
        <div
          v-for="member in members"
          :key="member.initials"
          class="w-7 h-7 rounded-full flex items-center justify-center text-[12px] font-bold ring-2 ring-surface-container-lowest"
          :class="[member.bg, member.fg]"
        >
          {{ member.initials }}
        </div>
      </div>
      <div class="flex flex-col">
        <span class="font-label-sm text-label-sm text-on-surface font-bold">{{ squadName }}</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">{{ role }}</span>
      </div>
    </div>
    <span class="font-label-sm text-label-sm text-secondary font-bold">{{ actNumber }}</span>
  </div>
</template>
