<script setup>
import { ref } from 'vue'

const emit = defineEmits(['open-upload'])

const helpAccepted = ref(false)

function acceptHelp() {
  helpAccepted.value = true
}
</script>

<template>
  <div class="flex flex-col gap-2.5 pt-2">
    <button
      class="w-full h-13 py-3.5 px-6 rounded-full font-label-lg text-label-lg font-bold shadow-md hover:opacity-95 active:scale-[0.98] transition-all flex items-center justify-center gap-3"
      :class="helpAccepted ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
      :disabled="helpAccepted"
      @click="acceptHelp"
    >
      <span class="material-symbols-outlined text-[22px]">{{ helpAccepted ? 'check_circle' : 'handshake' }}</span>
      <span>{{ helpAccepted ? 'Заявка в отряд принята' : 'Я готов помочь в выезде' }}</span>
    </button>

    <button
      class="w-full h-11 py-2.5 px-6 rounded-full bg-secondary-container text-on-secondary-container font-label-lg text-label-lg font-bold hover:bg-secondary-fixed transition-colors flex items-center justify-center gap-2.5"
      @click="emit('open-upload')"
    >
      <span class="material-symbols-outlined text-[20px]">upload_file</span>
      <span>Дополнить архивными данными</span>
    </button>

    <div class="flex items-center justify-center gap-4 pt-1">
      <button class="text-on-surface-variant hover:text-on-surface font-label-sm text-label-sm flex items-center gap-1 transition-colors">
        <span class="material-symbols-outlined text-[16px]">share</span>
        <span>Поделиться карточкой боя</span>
      </button>
      <span class="text-surface-container-highest">•</span>
      <button class="text-on-surface-variant hover:text-on-surface font-label-sm text-label-sm flex items-center gap-1 transition-colors">
        <span class="material-symbols-outlined text-[16px]">print</span>
        <span>Печать сводного листа</span>
      </button>
    </div>
  </div>
</template>
