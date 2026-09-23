<template>
  <!--
    Экран без вкладок и шапки — сейчас это только вход.

    Высота фиксированная (`h-screen` с уточнением в `dvh`, чтобы на телефоне
    не считалась вместе со свернувшейся адресной строкой), а не минимальная:
    иначе `flex-1` внутри не знает, сколько места осталось, и растягивающиеся
    блоки — маскот на входе — раздвигают страницу вместо того, чтобы ужаться.
  -->
  <div class="relative mx-auto flex h-screen h-[100dvh] w-full max-w-app flex-col overflow-hidden bg-parchment">
    <main class="pt-safe pb-safe flex w-full min-h-0 flex-1 flex-col bg-transparent">
      <slot />
    </main>
  </div>
</template>
