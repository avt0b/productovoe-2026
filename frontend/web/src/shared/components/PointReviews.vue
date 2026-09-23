<script setup>
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  point: { type: Object, required: true },
})

// Ни в одном сервисе нет сущности «отзыв о точке» — демо-заглушка целиком,
// хранится только в этом браузере, отдельно на каждую точку (по её id).
// Общий компонент для всех карт (слой «ВОВ», «Последний бой», экскурсии) —
// id точек в разных сервисах не пересекаются (разные UUID-таблицы), общий
// префикс ключа этого не портит.
function storageKey(pointId) {
  return `marshruty.point-reviews.${pointId}`
}

const reviews = reactive({ items: [] })

function load(pointId) {
  reviews.items = []
  if (!pointId) return
  try {
    const raw = localStorage.getItem(storageKey(pointId))
    reviews.items = raw ? JSON.parse(raw) : []
  } catch {
    reviews.items = []
  }
}

function persist() {
  try {
    localStorage.setItem(storageKey(props.point.id), JSON.stringify(reviews.items))
  } catch {
    // приватный режим браузера / переполненное хранилище — не критично для демо
  }
}

watch(() => props.point?.id, load, { immediate: true })

const form = reactive({ author: '', rating: 5, text: '' })

function submit() {
  if (!form.text.trim()) return
  reviews.items = [
    {
      id: crypto.randomUUID(),
      author: form.author.trim() || 'Аноним',
      rating: form.rating,
      text: form.text.trim(),
      created_at: new Date().toISOString(),
    },
    ...reviews.items,
  ]
  persist()
  form.author = ''
  form.rating = 5
  form.text = ''
}

const average = computed(() => {
  if (!reviews.items.length) return null
  return (reviews.items.reduce((sum, r) => sum + r.rating, 0) / reviews.items.length).toFixed(1)
})

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center gap-2 flex-wrap">
      <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Отзывы посетителей</span>
      <span class="px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-bold normal-case">
        демо — хранится только в этом браузере
      </span>
      <span v-if="average" class="flex items-center gap-1 font-label-sm text-label-sm font-bold text-tertiary ml-auto">
        <span class="material-symbols-outlined text-[16px]" style="font-variation-settings: 'FILL' 1">star</span>
        {{ average }} · {{ reviews.items.length }}
      </span>
    </div>

    <p v-if="!reviews.items.length" class="font-body-sm text-body-sm text-on-surface-variant">
      Пока никто не оставил отзыв об этой точке.
    </p>

    <div v-else class="flex flex-col gap-2 max-h-64 overflow-y-auto">
      <div v-for="r in reviews.items" :key="r.id" class="bg-surface-container-low p-3 rounded-DEFAULT flex flex-col gap-1">
        <div class="flex items-center justify-between gap-2">
          <span class="font-label-md text-label-md text-on-surface font-bold">{{ r.author }}</span>
          <div class="flex items-center gap-0.5">
            <span
              v-for="n in 5"
              :key="n"
              class="material-symbols-outlined text-[14px]"
              :class="n <= r.rating ? 'text-tertiary' : 'text-outline-variant'"
              :style="n <= r.rating ? { fontVariationSettings: `'FILL' 1` } : {}"
            >
              star
            </span>
          </div>
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant">{{ r.text }}</p>
        <span class="font-label-sm text-label-sm text-on-surface-variant">{{ formatDate(r.created_at) }}</span>
      </div>
    </div>

    <form class="flex flex-col gap-2 pt-2 border-t border-surface-container-high" @submit.prevent="submit">
      <div class="flex items-center gap-2">
        <span class="font-label-sm text-label-sm text-on-surface-variant">Оценка:</span>
        <button
          v-for="n in 5"
          :key="n"
          type="button"
          class="material-symbols-outlined text-[20px] transition-colors"
          :class="n <= form.rating ? 'text-tertiary' : 'text-outline-variant hover:text-tertiary/60'"
          :style="n <= form.rating ? { fontVariationSettings: `'FILL' 1` } : {}"
          @click="form.rating = n"
        >
          star
        </button>
      </div>
      <input
        v-model="form.author"
        type="text"
        placeholder="Ваше имя (необязательно)"
        class="w-full h-10 px-3.5 rounded-full bg-surface-container-low font-body-sm text-body-sm text-on-surface outline-none focus:bg-surface-container transition-colors"
      />
      <textarea
        v-model="form.text"
        rows="2"
        placeholder="Поделитесь впечатлением о посещении этой точки"
        class="w-full px-3.5 py-2.5 rounded-DEFAULT bg-surface-container-low font-body-sm text-body-sm text-on-surface outline-none focus:bg-surface-container transition-colors resize-none"
      />
      <button
        type="submit"
        class="self-start px-4 py-1.5 rounded-full bg-primary text-on-primary font-label-sm text-label-sm font-bold flex items-center gap-1.5"
      >
        <span class="material-symbols-outlined text-[16px]">send</span>
        Оставить отзыв
      </button>
    </form>
  </div>
</template>
