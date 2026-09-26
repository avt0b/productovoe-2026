<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { GrantedRole } from '../api'
import { RANKS } from '../ranks'

/**
 * Полноэкранный праздник «Звание присвоено».
 *
 * Сюжет на ~2,5 секунды: снизу, откуда приложили метку, расходится вспышка
 * цвета звания (олива — поисковик, золото — краевед), за спиной крутятся
 * лучи, совёнок выпрыгивает и подпрыгивает, сыплется конфетти, звание
 * шлёпается печатью, по одной выезжают строки «теперь вам доступно», и
 * только потом — кнопки. Сам не закрывается: его показывают судьям.
 * Нажатие по экрану проматывает к концу.
 */
const props = defineProps<{
  role: GrantedRole
  /** Имя для приветствия. */
  name: string
  /** Роль уже была — празднуем, но честно говорим, что ничего не поменялось. */
  already: boolean
}>()

const emit = defineEmits<{ profile: []; close: [] }>()

const rank = computed(() => RANKS[props.role])

/** Сколько длится уход, мс: гаснет быстрее, чем появлялось. */
const LEAVE_MS = 260

/**
 * Конфетти. Разброс — детерминированный по номеру, а не `Math.random()`:
 * каждый показ одинаковый, и на слабом телефоне нечего пересчитывать.
 */
const confetti = Array.from({ length: 36 }, (_, index) => ({
  left: `${(index * 37 + 11) % 100}%`,
  delay: `${400 + ((index * 53) % 1600)}ms`,
  duration: `${2600 + ((index * 71) % 1900)}ms`,
  drift: `${((index * 29) % 80) - 40}px`,
  spin: `${360 + ((index * 47) % 540)}deg`,
  tone: index % 5,
  wide: index % 3 === 0,
}))

const skipped = ref(false)
const leaving = ref(false)
const profileButton = ref<HTMLButtonElement | null>(null)
let timer: ReturnType<typeof setTimeout> | undefined

function leave(event: 'profile' | 'close'): void {
  if (leaving.value) return
  leaving.value = true
  timer = setTimeout(() => (event === 'profile' ? emit('profile') : emit('close')), LEAVE_MS)
}

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') leave('close')
}

onMounted(() => {
  // «Та-та-таам»: две коротких и длинная. На iPhone и компьютере вибрации нет — не страшно.
  navigator.vibrate?.([80, 60, 80, 60, 320])
  profileButton.value?.focus({ preventScroll: true })
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  clearTimeout(timer)
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <div
      class="rank"
      :class="[`rank--${role}`, { 'rank--skip': skipped, 'rank--leaving': leaving }]"
      role="alertdialog"
      aria-modal="true"
      :aria-label="`${already ? 'Звание подтверждено' : 'Звание присвоено'}: ${rank.title}`"
      @click="skipped = true"
    >
      <div class="rank__flash" aria-hidden="true" />
      <div class="rank__rays" aria-hidden="true" />

      <div class="rank__confetti" aria-hidden="true">
        <span
          v-for="(piece, index) in confetti"
          :key="index"
          class="rank__piece"
          :class="[`rank__piece--${piece.tone}`, { 'rank__piece--wide': piece.wide }]"
          :style="{
            left: piece.left,
            animationDelay: piece.delay,
            animationDuration: piece.duration,
            '--drift': piece.drift,
            '--spin': piece.spin,
          }"
        />
      </div>

      <div class="rank__stage">
        <div class="rank__hero">
          <div class="rank__glow" aria-hidden="true" />
          <div class="rank__hop">
            <img class="rank__chick" src="/mascot/celebrate-hd.webp" alt="" draggable="false" />
          </div>
        </div>

        <p class="rank__kicker rank__reveal">{{ already ? 'Звание подтверждено' : 'Звание присвоено' }}</p>
        <h2 class="rank__stamp rank__reveal">
          <MsIcon :name="rank.icon" :size="30" filled />
          <span>{{ rank.title }}</span>
        </h2>
        <p class="rank__name rank__reveal">
          <template v-if="already">{{ name }}, вы уже {{ rank.title.toLowerCase() }} — всё на месте</template>
          <template v-else>{{ name }}, поздравляем!</template>
        </p>

        <ul class="rank__perks" aria-label="Теперь вам доступно">
          <li
            v-for="(perk, index) in rank.perks"
            :key="perk.text"
            class="rank__perk rank__reveal"
            :style="{ animationDelay: `${1450 + index * 160}ms` }"
          >
            <MsIcon :name="perk.icon" :size="20" />
            <span>{{ perk.text }}</span>
          </li>
        </ul>
      </div>

      <div class="rank__actions rank__reveal">
        <button
          ref="profileButton"
          type="button"
          class="flex w-full items-center justify-center gap-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] short:py-2.5"
          @click.stop="leave('profile')"
        >
          <MsIcon name="person" :size="20" />
          В профиль
        </button>
        <button type="button" class="rank__later" @click.stop="leave('close')">Продолжить</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.rank {
  --rank-glow: theme('colors.secondary-fixed-dim');
  --rank-mid: theme('colors.secondary');
  --rank-deep: theme('colors.on-secondary-fixed');
  --rank-flash: theme('colors.secondary-fixed');

  position: fixed;
  inset: 0;
  /* Выше плашек тревоги (1400) и уведомлений (1500): праздник на весь экран. */
  z-index: 2100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: calc(env(safe-area-inset-top, 0px) + 16px) 20px calc(env(safe-area-inset-bottom, 0px) + 20px);
  color: theme('colors.inverse-on-surface');
  background: radial-gradient(circle at 50% 108%, var(--rank-glow) 0%, var(--rank-mid) 38%, var(--rank-deep) 100%);
  animation: rank-fade-in 300ms ease-out both;
}

.rank--local_historian {
  --rank-glow: theme('colors.tertiary-fixed-dim');
  --rank-mid: theme('colors.tertiary');
  --rank-deep: theme('colors.on-tertiary-fixed');
  --rank-flash: theme('colors.tertiary-fixed');
}

.rank--leaving {
  animation: rank-fade-out 260ms ease-in both;
}

/* Вспышка снизу — оттуда, где к телефону приложили метку. */
.rank__flash {
  position: absolute;
  left: 50%;
  bottom: -12vmax;
  width: 24vmax;
  height: 24vmax;
  margin-left: -12vmax;
  border-radius: 9999px;
  background: var(--rank-flash);
  opacity: 0;
  animation: rank-flash 1100ms cubic-bezier(0.2, 0.7, 0.3, 1) both;
}

.rank__rays {
  position: absolute;
  top: 30%;
  left: 50%;
  width: 180vmax;
  height: 180vmax;
  margin: -90vmax 0 0 -90vmax;
  background: repeating-conic-gradient(
    from 0deg,
    theme('colors.inverse-on-surface / 14%') 0deg 7deg,
    transparent 7deg 18deg
  );
  -webkit-mask-image: radial-gradient(circle, #000 0%, #000 12%, transparent 42%);
  mask-image: radial-gradient(circle, #000 0%, #000 12%, transparent 42%);
  opacity: 0;
  animation:
    rank-rays-in 900ms ease-out 200ms forwards,
    rank-spin 40s linear infinite;
}

.rank__confetti {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.rank__piece {
  position: absolute;
  top: -24px;
  width: 8px;
  height: 14px;
  border-radius: 2px;
  opacity: 0;
  animation-name: rank-confetti;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
  animation-fill-mode: both;
}

.rank__piece--wide {
  width: 14px;
  height: 8px;
}

.rank__piece--0 { background: theme('colors.primary-container'); }
.rank__piece--1 { background: theme('colors.tertiary-fixed-dim'); }
.rank__piece--2 { background: theme('colors.tertiary-fixed'); }
.rank__piece--3 { background: theme('colors.secondary-fixed-dim'); }
.rank__piece--4 { background: theme('colors.inverse-on-surface'); }

.rank__stage {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.rank__hero {
  position: relative;
  display: flex;
  justify-content: center;
  animation: rank-chick-in 750ms cubic-bezier(0.34, 1.56, 0.64, 1) 300ms both;
}

.rank__glow {
  position: absolute;
  inset: 12% 8% 0;
  border-radius: 9999px;
  background: radial-gradient(circle, theme('colors.inverse-on-surface / 45%') 0%, transparent 68%);
  filter: blur(6px);
}

/* Два радостных подпрыга после появления. */
.rank__hop {
  position: relative;
  animation: rank-hop 520ms ease-in-out 1100ms 2;
}

.rank__chick {
  display: block;
  height: min(34vh, 300px);
  width: auto;
  user-select: none;
  filter: drop-shadow(0 10px 18px theme('colors.inverse-surface / 35%'));
}

.rank__reveal {
  animation: rank-rise 450ms cubic-bezier(0.2, 0.7, 0.3, 1) both;
}

.rank__kicker {
  margin-top: 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: theme('colors.inverse-on-surface / 80%');
  animation-delay: 800ms;
}

/* Звание — печатью: влетает крупным, чуть повёрнутым, и «шлёпается». */
.rank__stamp {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  padding: 6px 18px;
  border: 3px solid currentColor;
  border-radius: 12px;
  font-size: clamp(2rem, 10vw, 2.75rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  transform: rotate(-3deg);
  box-shadow: 0 6px 22px theme('colors.inverse-surface / 30%');
  animation: rank-stamp 520ms cubic-bezier(0.3, 1.4, 0.5, 1) 950ms both;
}

.rank__name {
  margin-top: 14px;
  max-width: 22rem;
  font-size: 1rem;
  font-weight: 600;
  animation-delay: 1250ms;
}

.rank__perks {
  display: flex;
  width: 100%;
  max-width: 22rem;
  flex-direction: column;
  gap: 8px;
  margin-top: 18px;
}

.rank__perk {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid theme('colors.inverse-on-surface / 18%');
  border-radius: 1rem;
  background: theme('colors.inverse-on-surface / 12%');
  font-size: 0.9rem;
  font-weight: 600;
  text-align: left;
  animation-name: rank-slide;
}

.rank__actions {
  position: relative;
  display: flex;
  width: 100%;
  max-width: 22rem;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  margin: 16px auto 0;
  animation-delay: 2300ms;
}

.rank__later {
  padding: 10px 16px;
  font: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  color: theme('colors.inverse-on-surface / 85%');
}

/* Нажали по экрану — сразу к концу: текст и кнопки без ожидания. */
.rank--skip .rank__reveal,
.rank--skip .rank__stamp {
  animation-delay: 0ms !important;
  animation-duration: 200ms !important;
}

/* Низкий экран: птица меньше, строки плотнее — кнопки не уезжают за край. */
@media (max-height: 740px) {
  .rank__chick {
    height: min(28vh, 220px);
  }

  .rank__stamp {
    font-size: clamp(1.75rem, 9vw, 2.25rem);
  }

  .rank__perks {
    gap: 6px;
    margin-top: 12px;
  }

  .rank__perk {
    padding: 7px 12px;
  }
}

@keyframes rank-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes rank-fade-out {
  from { opacity: 1; }
  to { opacity: 0; transform: scale(1.02); }
}

@keyframes rank-flash {
  0% { opacity: 0.9; transform: scale(0.2); }
  100% { opacity: 0; transform: scale(9); }
}

@keyframes rank-rays-in {
  to { opacity: 1; }
}

@keyframes rank-spin {
  to { rotate: 360deg; }
}

@keyframes rank-confetti {
  0% { opacity: 0; transform: translate3d(0, 0, 0) rotate(0deg); }
  8% { opacity: 1; }
  100% { opacity: 1; transform: translate3d(var(--drift), 110vh, 0) rotate(var(--spin)); }
}

@keyframes rank-chick-in {
  0% { opacity: 0; transform: translateY(45%) scale(0.6); }
  60% { opacity: 1; }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes rank-hop {
  0%, 100% { transform: translateY(0); }
  45% { transform: translateY(-16px) rotate(-2deg); }
}

@keyframes rank-rise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes rank-slide {
  from { opacity: 0; transform: translateX(-24px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes rank-stamp {
  0% { opacity: 0; transform: scale(1.9) rotate(-10deg); }
  60% { opacity: 1; transform: scale(0.94) rotate(-2deg); }
  100% { opacity: 1; transform: scale(1) rotate(-3deg); }
}

/* Уменьшенное движение: без прыжков, лучей и конфетти — просто появление. */
@media (prefers-reduced-motion: reduce) {
  .rank__rays,
  .rank__confetti,
  .rank__flash {
    display: none;
  }

  .rank__hero,
  .rank__hop,
  .rank__reveal,
  .rank__stamp {
    animation-name: rank-fade-in !important;
  }

  .rank__stamp {
    transform: rotate(-3deg);
  }
}
</style>
