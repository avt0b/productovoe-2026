<script setup lang="ts">
import { computed } from 'vue'

import { mascotSrc, type MascotPose } from './mascot'

/**
 * Совёнок-следопыт на экране.
 *
 * Высота — пропсом в пикселях, как у `MsIcon`: маскот стоит на экранах разного
 * масштаба, от строки в профиле до карточки обучения во весь экран, и классы
 * под каждый случай расползлись бы по разметке.
 *
 * По умолчанию картинка декоративная: рядом всегда есть заголовок и текст,
 * которые говорят то же самое, а вторая подпись в скринридере — помеха.
 */
const props = withDefaults(
  defineProps<{
    pose: MascotPose
    /** Высота картинки в пикселях. */
    size?: number
    /** Подпись для скринридера. Пусто — картинка декоративная. */
    alt?: string
  }>(),
  { size: 120, alt: '' },
)

const src = computed(() => mascotSrc(props.pose))
</script>

<template>
  <img
    :src="src"
    :alt="alt"
    :aria-hidden="alt ? undefined : true"
    :style="{ height: `${size}px` }"
    class="max-h-[30vh] w-auto shrink-0 select-none object-contain drop-shadow-[0_10px_18px_rgba(92,69,32,0.18)]"
    decoding="async"
    draggable="false"
  />
</template>
