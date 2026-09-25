<script setup lang="ts">
import { ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

/** Оценка экскурсии: звёзды обязательны, отзыв — по желанию. */
defineProps<{ busy: boolean }>()

const emit = defineEmits<{ close: []; submit: [rating: number, comment: string] }>()

const rating = ref(0)
const comment = ref('')

const TITLES = ['', 'Не понравилось', 'Так себе', 'Нормально', 'Хорошо', 'Отлично']
</script>

<template>
  <SheetDialog title="Как прошла экскурсия?" subtitle="Оценка видна другим — по ней выбирают, к кому пойти" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="rating > 0 && emit('submit', rating, comment.trim())">
      <div class="flex flex-col items-center gap-space-xs">
        <div class="flex items-center gap-space-xs">
          <button
            v-for="star in 5"
            :key="star"
            type="button"
            class="flex h-11 w-11 items-center justify-center rounded-full transition-transform active:scale-90"
            :class="star <= rating ? 'text-tertiary' : 'text-outline-variant'"
            :aria-label="`${star} из 5`"
            :aria-pressed="star === rating"
            @click="rating = star"
          >
            <MsIcon :name="star <= rating ? 'star' : 'star_border'" :size="32" :filled="star <= rating" />
          </button>
        </div>
        <p class="h-5 font-label-md text-label-md text-on-surface-variant">{{ TITLES[rating] }}</p>
      </div>

      <FormTextarea
        v-model="comment"
        label="Отзыв"
        placeholder="Что запомнилось, что стоит поправить"
        :rows="3"
        :maxlength="500"
        hint="Не обязательно"
      />

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-60"
        :disabled="busy || rating === 0"
      >
        <MsIcon :name="busy ? 'progress_activity' : 'send'" :size="20" :class="{ 'animate-spin': busy }" />
        Отправить оценку
      </button>
    </form>
  </SheetDialog>
</template>
