<script setup></script>

<template>
  <RouterLink
    to="/excursions"
    class="bg-surface-container-lowest rounded-lg p-6 shadow-sm hover:shadow-md transition-all flex items-center justify-between gap-4 group"
  >
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-full bg-primary-fixed text-on-primary-fixed flex items-center justify-center shrink-0">
        <span class="material-symbols-outlined text-[24px]">groups_3</span>
      </div>
      <div class="flex flex-col">
        <span class="font-headline-sm text-headline-sm text-on-surface font-bold group-hover:text-primary transition-colors">
          Заявки школ на экскурсии
        </span>
        <span class="font-body-sm text-body-sm text-on-surface-variant">
          Индивидуальная или коллективная запись на экскурсию с гидом — на отдельной вкладке
        </span>
      </div>
    </div>
    <span class="material-symbols-outlined text-primary text-[22px] shrink-0 group-hover:translate-x-1 transition-transform">
      arrow_forward
    </span>
  </RouterLink>
</template>
