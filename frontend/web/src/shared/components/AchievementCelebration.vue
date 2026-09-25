<script setup>
import { computed } from 'vue'
import { useAchievementCelebration } from '../composables/useAchievementCelebration.js'

const { active, title } = useAchievementCelebration()

const COLORS = ['bg-primary', 'bg-secondary', 'bg-tertiary', 'bg-ribbon-orange', 'bg-error', 'bg-ribbon-orange-deep']

// Несколько точек залпа в случайных местах экрана — каждая со своим набором
// разлетающихся частиц. Пересчитывается заново при каждом celebrate(), пока
// оверлей открыт (computed зависит от active, а title меняется вместе с ним).
const bursts = computed(() => {
  if (!active.value) return []
  return Array.from({ length: 5 }, (_, i) => ({
    id: i,
    left: `${10 + Math.random() * 80}%`,
    top: `${10 + Math.random() * 50}%`,
    delay: `${i * 90}ms`,
    particles: Array.from({ length: 16 }, (_, p) => ({
      id: p,
      angle: `${(360 / 16) * p + Math.random() * 12}deg`,
      distance: `${70 + Math.random() * 50}px`,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
    })),
  }))
})
</script>

<template>
  <Teleport to="body">
    <div v-if="active" class="fixed inset-0 z-[100] pointer-events-none overflow-hidden">
      <div
        v-for="burst in bursts"
        :key="burst.id"
        class="absolute w-0 h-0"
        :style="{ left: burst.left, top: burst.top, animationDelay: burst.delay }"
      >
        <span
          v-for="p in burst.particles"
          :key="p.id"
          class="celebration-particle absolute w-2 h-2 rounded-full"
          :class="p.color"
          :style="{ '--angle': p.angle, '--distance': p.distance, animationDelay: burst.delay }"
        />
      </div>

      <div class="absolute top-4 inset-x-0 flex justify-center px-4">
        <div
          class="celebration-toast flex items-center gap-3 bg-surface-container-lowest text-on-surface px-5 py-3 rounded-full shadow-sheet"
        >
          <span class="material-symbols-outlined text-tertiary text-[24px]" style="font-variation-settings: 'FILL' 1">
            military_tech
          </span>
          <div class="flex flex-col leading-tight">
            <span class="font-label-sm text-label-sm text-on-surface-variant uppercase font-bold">Новое достижение</span>
            <span class="font-label-lg text-label-lg font-bold">{{ title }}</span>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.celebration-particle {
  animation: celebration-burst 1100ms ease-out forwards;
  transform: rotate(var(--angle)) translateY(0);
}

@keyframes celebration-burst {
  0% {
    opacity: 1;
    transform: rotate(var(--angle)) translateY(0) scale(1);
  }
  70% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: rotate(var(--angle)) translateY(calc(-1 * var(--distance))) scale(0.3);
  }
}

.celebration-toast {
  animation:
    celebration-toast-in 300ms ease-out forwards,
    celebration-toast-out 300ms ease-in forwards 1700ms;
}

@keyframes celebration-toast-in {
  from {
    opacity: 0;
    transform: translateY(-16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes celebration-toast-out {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-16px);
  }
}
</style>
