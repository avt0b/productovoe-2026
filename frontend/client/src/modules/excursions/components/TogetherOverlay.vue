<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

/**
 * Полноэкранная анимация «Вы вместе!» после совпавшего бампа.
 *
 * Временная, текстовая: два телефона сходятся, от точки встречи расходятся
 * круги, буквы заголовка выпрыгивают по одной. Настоящую иллюстрацию нарисуем
 * позже — заменится только этот компонент, экран сбора его просто показывает.
 */
const props = withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    /** Через сколько закрыться самой, мс. */
    durationMs?: number
  }>(),
  { title: 'Вы вместе!', subtitle: '', durationMs: 3600 },
)

const emit = defineEmits<{ close: [] }>()

/** Пробелы — неразрывные: иначе у буквы-спана с пробелом нет ширины. */
const letters = computed(() => [...props.title].map((char) => (char === ' ' ? ' ' : char)))

const closeButton = ref<HTMLButtonElement | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined

onMounted(() => {
  timer = setTimeout(() => emit('close'), props.durationMs)
  // Короткая дробь вибрацией: «тук-тук — вместе». На iPhone и компьютере её нет — не страшно.
  navigator.vibrate?.([60, 50, 60, 50, 180])
  closeButton.value?.focus()
})

onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <Teleport to="body">
    <div class="together" role="alertdialog" aria-modal="true" :aria-label="`${title} ${subtitle}`" @click="emit('close')">
      <div class="together__rings" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>

      <div class="together__phones" aria-hidden="true">
        <span class="together__phone together__phone--left">
          <MsIcon name="smartphone" :size="44" />
        </span>
        <span class="together__phone together__phone--right">
          <MsIcon name="smartphone" :size="44" />
        </span>
      </div>

      <h2 class="together__title">
        <span
          v-for="(letter, index) in letters"
          :key="index"
          class="together__letter"
          :style="{ animationDelay: `${650 + index * 55}ms` }"
        >
          {{ letter }}
        </span>
      </h2>

      <p v-if="subtitle" class="together__subtitle">{{ subtitle }}</p>

      <button ref="closeButton" type="button" class="together__close" @click.stop="emit('close')">
        Нажмите, чтобы закрыть
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
.together {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 24px;
  text-align: center;
  color: theme('colors.inverse-on-surface');
  background: radial-gradient(circle at 50% 42%, theme('colors.primary') 0%, theme('colors.on-primary-fixed-variant') 45%, theme('colors.inverse-surface') 100%);
  animation: together-fade-in 250ms ease-out both;
}

.together__rings {
  position: absolute;
  top: 38%;
  left: 50%;
  width: 0;
  height: 0;
}

.together__rings span {
  position: absolute;
  left: -60px;
  top: -60px;
  width: 120px;
  height: 120px;
  border: 3px solid theme('colors.tertiary-fixed');
  border-radius: 9999px;
  opacity: 0;
  animation: together-ring 1600ms ease-out infinite;
  animation-delay: 550ms;
}

.together__rings span:nth-child(2) {
  animation-delay: 950ms;
}

.together__rings span:nth-child(3) {
  animation-delay: 1350ms;
}

.together__phones {
  position: relative;
  width: 160px;
  height: 72px;
  margin-bottom: 28px;
}

.together__phone {
  position: absolute;
  top: 0;
  display: flex;
  width: 72px;
  height: 72px;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  color: theme('colors.primary');
  background: theme('colors.surface-container-lowest');
  box-shadow: 0 10px 30px rgb(0 0 0 / 0.3);
}

.together__phone--left {
  left: 0;
  animation: together-phone-left 650ms cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.together__phone--right {
  right: 0;
  animation: together-phone-right 650ms cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.together__title {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  margin: 0;
  font-family: inherit;
  font-size: 3rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.together__letter {
  display: inline-block;
  opacity: 0;
  animation: together-letter 520ms cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

.together__subtitle {
  max-width: 20rem;
  margin: 16px 0 0;
  font-size: 1rem;
  line-height: 1.45;
  opacity: 0;
  animation: together-fade-in 400ms ease-out 1300ms both;
}

.together__close {
  position: absolute;
  bottom: calc(env(safe-area-inset-bottom, 0px) + 32px);
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  font-size: 0.8rem;
  opacity: 0.6;
}

@keyframes together-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes together-phone-left {
  0% {
    transform: translateX(-140px) rotate(-20deg);
  }
  70% {
    transform: translateX(34px) rotate(8deg);
  }
  100% {
    transform: translateX(26px) rotate(0);
  }
}

@keyframes together-phone-right {
  0% {
    transform: translateX(140px) rotate(20deg);
  }
  70% {
    transform: translateX(-34px) rotate(-8deg);
  }
  100% {
    transform: translateX(-26px) rotate(0);
  }
}

@keyframes together-ring {
  0% {
    transform: scale(0.3);
    opacity: 0.9;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

@keyframes together-letter {
  0% {
    transform: translateY(40px) scale(0.3);
    opacity: 0;
  }
  60% {
    transform: translateY(-8px) scale(1.2);
    opacity: 1;
  }
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

/* Без движения: только появление, текст сразу на месте. */
@media (prefers-reduced-motion: reduce) {
  .together__phone,
  .together__letter,
  .together__subtitle,
  .together__rings span {
    animation: none;
    opacity: 1;
  }

  .together__rings {
    display: none;
  }
}
</style>
