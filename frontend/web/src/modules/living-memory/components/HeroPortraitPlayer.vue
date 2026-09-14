<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import SmartImage from '@shared/components/SmartImage.vue'

defineProps({
  portraitUrl: { type: String, default: 'https://loremflickr.com/600/800/soldier?lock=204' },
  quote: { type: String, default: '«Я сделал это, чтобы ты жил и видел мирное небо. Помни меня.»' },
  quoteSource: { type: String, default: 'Голосовая реконструкция по письмам 1941 г.' },
  progressLabel: { type: String, default: '0:24 / 1:18' },
})

const rates = ['1.0x', '1.25x', '1.5x', '0.75x']
const isPlaying = ref(true)
const isMuted = ref(false)
const rateIdx = ref(0)
const barHeights = ref(Array.from({ length: 29 }, () => 4 + Math.floor(Math.random() * 28)))

let waveformTimer

function togglePlay() {
  isPlaying.value = !isPlaying.value
}

function toggleMute() {
  isMuted.value = !isMuted.value
}

function cycleRate() {
  rateIdx.value = (rateIdx.value + 1) % rates.length
}

function replay() {
  isPlaying.value = true
}

onMounted(() => {
  waveformTimer = setInterval(() => {
    if (isPlaying.value) {
      barHeights.value = barHeights.value.map(() => 4 + Math.floor(Math.random() * 28))
    }
  }, 350)
})

onUnmounted(() => clearInterval(waveformTimer))
</script>

<template>
  <div class="relative w-full rounded-lg overflow-hidden bg-inverse-surface text-inverse-on-surface shadow-xl flex flex-col">
    <div class="relative w-full aspect-[3/4] bg-surface-dim overflow-hidden group">
      <SmartImage
        :src="portraitUrl"
        icon="portrait"
        img-class="w-full h-full object-cover object-top transition-transform duration-700 group-hover:scale-105"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-inverse-surface via-transparent to-black/30 pointer-events-none" />

      <div class="absolute top-4 left-4 right-4 flex items-center justify-between z-10">
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md font-label-sm text-label-sm text-white font-bold flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[15px] text-tertiary-fixed">smart_toy</span>
            Нейрореставрация • 60 FPS
          </span>
          <span class="px-2.5 py-1 rounded-full bg-primary/80 backdrop-blur-md font-label-sm text-label-sm text-white font-bold flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[15px]">record_voice_over</span>
            Аутентичный голос
          </span>
        </div>
        <button class="w-8 h-8 rounded-full bg-black/40 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/70 transition-colors">
          <span class="material-symbols-outlined text-[18px]">fullscreen</span>
        </button>
      </div>

      <div class="absolute bottom-3 left-4 right-4 z-10">
        <div class="bg-black/75 backdrop-blur-md rounded-DEFAULT p-3.5 shadow-md">
          <div class="flex items-start gap-2.5">
            <span class="material-symbols-outlined text-tertiary-fixed text-[20px] shrink-0 mt-0.5">format_quote</span>
            <p class="font-body-md text-body-md text-white/95 italic leading-snug">{{ quote }}</p>
          </div>
          <div class="flex items-center justify-between mt-2 pt-2 border-t border-white/10 text-white/70 font-label-sm text-label-sm">
            <span>{{ quoteSource }}</span>
            <span class="text-tertiary-fixed font-bold">{{ progressLabel }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="p-5 flex flex-col gap-4 bg-inverse-surface">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <button
            class="w-12 h-12 rounded-full bg-primary text-on-primary flex items-center justify-center shadow-lg hover:bg-primary-container transition-transform active:scale-95"
            @click="togglePlay"
          >
            <span class="material-symbols-outlined text-[26px]">{{ isPlaying ? 'pause' : 'play_arrow' }}</span>
          </button>
          <button
            class="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors"
            @click="replay"
          >
            <span class="material-symbols-outlined text-[20px]">replay_10</span>
          </button>
          <button
            class="px-2.5 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white font-label-md text-label-md flex items-center justify-center transition-colors"
            @click="cycleRate"
          >
            {{ rates[rateIdx] }}
          </button>
        </div>
        <div class="flex items-center gap-3">
          <button
            class="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors"
            @click="toggleMute"
          >
            <span class="material-symbols-outlined text-[20px]">{{ isMuted ? 'volume_off' : 'volume_up' }}</span>
          </button>
          <div class="w-24 h-1.5 bg-white/20 rounded-full overflow-hidden relative cursor-pointer">
            <div class="h-full bg-primary w-3/4 rounded-full" />
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <div class="flex items-center justify-between text-white/60 font-label-sm text-label-sm">
          <span class="flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px]">graphic_eq</span>
            Аудиоволна памяти
          </span>
          <span>Частотная гармоника: 432 Hz</span>
        </div>
        <div class="h-10 w-full flex items-end gap-1 px-1 py-1 bg-white/5 rounded-DEFAULT overflow-hidden cursor-pointer">
          <div
            v-for="(h, i) in barHeights"
            :key="i"
            class="w-1 bg-primary rounded-full transition-all duration-300"
            :class="{ 'bg-primary/40': i >= 16 }"
            :style="{ height: h + 'px' }"
          />
        </div>
      </div>
    </div>
  </div>
</template>
