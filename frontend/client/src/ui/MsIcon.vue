<script setup lang="ts">
/**
 * Иконка Material Symbols.
 *
 * Размер — пропсом в пикселях, а не классом `text-[20px]`: в макете у иконок
 * десяток разных размеров, и произвольные значения расползлись бы по разметке.
 */
withDefaults(
  defineProps<{
    name: string
    size?: number
    /** Залитый вариант — в макете так отмечены активные и «наградные» иконки. */
    filled?: boolean
  }>(),
  { size: 24, filled: false },
)
</script>

<template>
  <span
    class="material-symbols-outlined select-none"
    :class="{ 'icon-filled': filled }"
    :style="{ fontSize: `${size}px` }"
    aria-hidden="true"
  >
    {{ name }}
  </span>
</template>
