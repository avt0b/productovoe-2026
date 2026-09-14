<script setup>
defineProps({
  project: { type: String, default: 'Проект «Живая память»' },
  caseNumber: { type: String, default: 'Архивное дело № 48-137-В' },
  quality: { type: String, default: 'Оцифровано в 4K Ultra HD' },
})
</script>

<template>
  <div class="flex items-center justify-between py-6 flex-wrap gap-4">
    <div class="flex items-center gap-3">
      <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-secondary-container text-on-secondary-container">
        <span class="material-symbols-outlined text-[18px]">history_edu</span>
      </span>
      <div class="flex items-center gap-2">
        <span class="font-label-sm text-label-sm text-secondary uppercase tracking-widest">{{ project }}</span>
        <span class="text-outline-variant font-bold">•</span>
        <span class="font-label-sm text-label-sm text-on-surface-variant">{{ caseNumber }}</span>
      </div>
    </div>
    <div class="flex items-center gap-2.5">
      <div class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm">
        <span class="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <span>{{ quality }}</span>
      </div>
      <button
        class="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface-container-low hover:bg-surface-container text-on-surface font-label-md text-label-md transition-all shadow-sm"
      >
        <span class="material-symbols-outlined text-[18px] text-tertiary">download</span>
        <span>Экспорт карточки</span>
      </button>
    </div>
  </div>
</template>
