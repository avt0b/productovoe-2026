<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import type { Contact } from '../data'

defineProps<{ contacts: Contact[] }>()
</script>

<template>
  <section class="mt-2 flex flex-col gap-space-sm">
    <div class="px-1">
      <h3 class="font-headline-sm text-headline-sm text-on-surface">Персональные данные</h3>
      <span class="font-body-sm text-body-sm text-on-surface-variant">Контактная информация полевого исследователя</span>
    </div>

    <div class="flex flex-col rounded-DEFAULT bg-surface-container-lowest p-space-md shadow-sm">
      <template v-for="(contact, index) in contacts" :key="contact.id">
        <div v-if="index > 0" class="my-space-md h-px bg-surface-container" />
        <div class="flex items-center justify-between gap-space-sm">
          <div class="flex min-w-0 items-center gap-space-sm">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container text-on-surface-variant">
              <MsIcon :name="contact.icon" :size="19" />
            </div>
            <div class="min-w-0">
              <span class="block font-label-sm text-label-sm text-outline">{{ contact.label }}</span>
              <span class="block truncate font-label-lg text-label-lg font-semibold text-on-surface">{{ contact.value }}</span>
            </div>
          </div>
          <button type="button" :aria-label="`Изменить: ${contact.label}`" class="text-on-surface-variant hover:text-primary">
            <MsIcon name="edit" :size="19" />
          </button>
        </div>
      </template>
    </div>
  </section>
</template>
