<script setup>
import SmartImage from '@shared/components/SmartImage.vue'

// name/role/squad/avatarUrl — реальные поля user_service (ProfileOut). Ранг,
// очки, жетон и т.п. убраны совсем: такого нет ни в одном сервисе, и вместо
// демо-заглушек в шапке профиля остаются только настоящие данные.
defineProps({
  name: { type: String, default: '' },
  role: { type: String, default: '' },
  squad: { type: String, default: '' },
  avatarUrl: { type: String, default: '' },
})
</script>

<template>
  <section class="relative rounded-lg overflow-hidden bg-secondary text-on-secondary shadow-md p-8 mb-8">
    <div class="absolute -right-24 -top-24 w-96 h-96 rounded-full bg-secondary-fixed/10 blur-3xl pointer-events-none" />
    <div class="absolute right-1/4 -bottom-20 w-80 h-80 rounded-full bg-primary/10 blur-2xl pointer-events-none" />

    <div class="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-8">
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-6">
        <div class="relative shrink-0">
          <div
            class="w-24 h-24 rounded-full overflow-hidden shadow-md ring-4 ring-secondary-fixed/30 bg-surface-container-high"
          >
            <SmartImage :src="avatarUrl" icon="person" img-class="w-full h-full object-cover" />
          </div>
        </div>

        <div class="flex flex-col">
          <div class="flex flex-wrap items-center gap-2.5 mb-1.5">
            <h1 class="font-headline-lg text-headline-lg text-on-secondary font-bold">{{ name || 'Без имени' }}</h1>
            <span
              v-if="role"
              class="bg-secondary-fixed/20 text-secondary-fixed px-3 py-0.5 rounded-full font-label-sm text-label-sm uppercase font-bold tracking-wide"
            >
              {{ role }}
            </span>
          </div>
          <p v-if="squad" class="font-body-md text-body-md text-secondary-fixed-dim mb-3">{{ squad }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
