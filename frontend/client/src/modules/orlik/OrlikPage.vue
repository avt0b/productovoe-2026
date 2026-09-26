<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import MsIcon from '@/ui/MsIcon.vue'

import { LETTER } from './letter'

/**
 * Благодарственное письмо на весь экран: орлик отдаёт честь, под ним письмо
 * команды. Открывается фигуркой с NFC-чипом (см. `index.ts`).
 */
const router = useRouter()

/**
 * Поза «салют» в большом размере: обычная (`/mascot/salute.png`, 512 px по
 * высоте) на полэкрана телефона расплывается.
 */
const ORLIK_SRC = '/mascot/salute-hd.webp'

/** Звёздочки вокруг орлика: вспыхивают по очереди, а не разом. */
const SPARKS = [
  { top: '10%', left: '10%', size: 18, delay: 700, tone: 'text-tertiary-fixed-dim' },
  { top: '4%', left: '80%', size: 22, delay: 1000, tone: 'text-primary-container' },
  { top: '42%', left: '2%', size: 14, delay: 1300, tone: 'text-primary-container' },
  { top: '36%', left: '88%', size: 16, delay: 1600, tone: 'text-tertiary-fixed-dim' },
  { top: '68%', left: '12%', size: 12, delay: 1900, tone: 'text-tertiary-fixed-dim' },
  { top: '64%', left: '84%', size: 12, delay: 2200, tone: 'text-primary-container' },
] as const

onMounted(() => {
  // Человек держит фигурку у телефона и на экран может ещё не смотреть.
  navigator.vibrate?.([60, 70, 140])
})

function close(): void {
  // Метка могла открыть приложение сразу здесь — тогда назад некуда.
  if (window.history.state?.back) router.back()
  else void router.replace({ name: 'home' })
}

function forward(): void {
  void router.replace({ name: 'home' })
}
</script>

<template>
  <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden">
    <div class="orlik-glow pointer-events-none absolute inset-x-0 top-0 h-[60%]" aria-hidden="true" />

    <button
      type="button"
      class="absolute right-space-md top-space-sm z-20 flex h-11 w-11 items-center justify-center rounded-full bg-surface-container-lowest/85 text-on-surface shadow-float backdrop-blur-sm active:scale-95"
      aria-label="Закрыть"
      @click="close"
    >
      <MsIcon name="close" :size="22" />
    </button>

    <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-space-md pb-space-md">
      <div class="relative z-10 mx-auto mt-space-lg flex h-[38vh] w-full max-w-[20rem] shrink-0 items-end justify-center short:mt-space-md short:h-[32vh]">
        <MsIcon
          v-for="(spark, index) in SPARKS"
          :key="index"
          name="star"
          filled
          :size="spark.size"
          class="orlik-spark absolute"
          :class="spark.tone"
          :style="{ top: spark.top, left: spark.left, animationDelay: `${spark.delay}ms` }"
          aria-hidden="true"
        />
        <img
          :src="ORLIK_SRC"
          alt="Орлик в каске отдаёт честь"
          class="orlik-rise h-full w-auto select-none object-contain drop-shadow-[0_14px_22px_rgba(92,69,32,0.25)]"
          draggable="false"
        />
      </div>

      <article class="orlik-letter relative -mt-space-lg rounded-2xl bg-surface-container-lowest px-space-lg pb-space-lg pt-space-xl shadow-document">
        <div class="orlik-ribbon absolute inset-x-0 top-0 h-2.5 rounded-t-2xl" aria-hidden="true" />

        <p class="font-archival text-archival uppercase text-tertiary">{{ LETTER.kicker }}</p>
        <h1
          class="ribbon-shimmer mt-space-xs font-headline-lg-mobile text-headline-lg-mobile [--shimmer-base:theme(colors.primary)]"
        >
          {{ LETTER.title }}
        </h1>

        <p class="mt-space-md font-headline-sm text-headline-sm text-on-surface">{{ LETTER.greeting }}</p>
        <p
          v-for="(paragraph, index) in LETTER.paragraphs"
          :key="index"
          class="mt-space-sm font-body-md text-body-md text-on-surface"
        >
          {{ paragraph }}
        </p>

        <div class="mt-space-lg flex items-end justify-between gap-space-md">
          <p class="font-body-sm text-body-sm text-on-surface-variant">
            {{ LETTER.signOff }}<br />
            <span class="font-label-lg text-label-lg text-on-surface">{{ LETTER.team }}</span>
          </p>
          <div
            class="orlik-seal flex h-16 w-16 shrink-0 -rotate-12 items-center justify-center rounded-full border-2 border-primary text-primary shadow-stamp"
            aria-hidden="true"
          >
            <MsIcon name="star" :size="30" filled />
          </div>
        </div>
      </article>
    </div>

    <div class="shrink-0 px-space-md pb-space-md pt-space-sm">
      <button
        type="button"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
        @click="forward"
      >
        <span>Вперёд!</span>
        <MsIcon name="arrow_forward" :size="20" />
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Наградная охра за орликом, растворяется в пергаменте. */
.orlik-glow {
  background: radial-gradient(58% 52% at 50% 46%, theme('colors.tertiary-fixed') 0%, transparent 72%);
}

/* Кромка письма в цветах георгиевской ленты. */
.orlik-ribbon {
  background: repeating-linear-gradient(
    to bottom,
    theme('colors.ink.DEFAULT') 0 2px,
    theme('colors.tertiary-fixed-dim') 2px 4px
  );
}

.orlik-rise {
  transform-origin: 50% 100%;
  animation:
    orlik-rise 900ms cubic-bezier(0.22, 1.25, 0.36, 1) both,
    orlik-breathe 4s ease-in-out 900ms infinite;
}

.orlik-letter {
  animation: orlik-letter 700ms ease-out 300ms both;
}

.orlik-seal {
  animation: orlik-seal 500ms cubic-bezier(0.3, 1.6, 0.5, 1) 1100ms both;
}

.orlik-spark {
  opacity: 0;
  animation: orlik-spark 2.8s ease-in-out infinite;
}

@keyframes orlik-rise {
  from {
    opacity: 0;
    transform: translateY(35%) scale(0.85);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes orlik-breathe {
  0%,
  100% {
    transform: none;
  }
  50% {
    transform: translateY(-1.5%) scale(1.01);
  }
}

@keyframes orlik-letter {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* Печать ставится с размаху: крупнее и прозрачной — на место. */
@keyframes orlik-seal {
  from {
    opacity: 0;
    transform: rotate(-12deg) scale(1.8);
  }
  to {
    opacity: 1;
    transform: rotate(-12deg) scale(1);
  }
}

@keyframes orlik-spark {
  0% {
    opacity: 0;
    transform: scale(0.3) rotate(0deg);
  }
  20% {
    opacity: 1;
    transform: scale(1) rotate(20deg);
  }
  45%,
  100% {
    opacity: 0;
    transform: scale(0.4) rotate(45deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .orlik-rise,
  .orlik-letter,
  .orlik-seal,
  .orlik-spark {
    animation: none;
  }

  .orlik-spark {
    opacity: 0.85;
  }
}
</style>
