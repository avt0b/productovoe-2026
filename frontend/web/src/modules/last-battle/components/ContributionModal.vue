<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const sent = ref(false)

function close() {
  emit('update:modelValue', false)
  sent.value = false
}

function send() {
  sent.value = true
  setTimeout(close, 1200)
}
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 bg-on-background/40 backdrop-blur-sm flex items-center justify-center p-4"
    @click.self="close"
  >
    <div class="bg-surface-container-lowest rounded-lg max-w-lg w-full p-6 shadow-2xl flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-[24px]">note_add</span>
          <h3 class="font-headline-sm text-headline-sm text-on-surface font-bold">Архивное свидетельство</h3>
        </div>
        <button
          class="w-8 h-8 rounded-full bg-surface-container hover:bg-surface-container-high text-on-surface flex items-center justify-center transition-colors"
          @click="close"
        >
          <span class="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      <p class="font-body-md text-body-md text-on-surface-variant">
        Прикрепите отсканированные письма, фотографии или выписки из ОБД «Мемориал», относящиеся к 9-й ВДБр и высоте 214.
      </p>

      <div class="p-6 rounded-DEFAULT bg-surface-container-low border-2 border-dashed border-outline-variant flex flex-col items-center justify-center gap-2 text-center cursor-pointer hover:bg-surface-container transition-colors">
        <span class="material-symbols-outlined text-primary text-[36px]">cloud_upload</span>
        <span class="font-label-md text-label-md font-bold text-on-surface">Перетащите файлы или выберите с устройства</span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">PDF, JPG, TIFF до 25 МБ</span>
      </div>

      <div class="flex justify-end gap-3 pt-2">
        <button class="px-5 py-2 rounded-full bg-surface-container text-on-surface font-label-md text-label-md" @click="close">
          Отмена
        </button>
        <button
          class="px-5 py-2 rounded-full font-label-md text-label-md font-bold shadow-sm"
          :class="sent ? 'bg-secondary text-on-secondary' : 'bg-primary text-on-primary'"
          @click="send"
        >
          {{ sent ? 'Передано историкам' : 'Отправить на модерацию' }}
        </button>
      </div>
    </div>
  </div>
</template>
