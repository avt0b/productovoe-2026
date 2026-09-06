<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AppShell from '@/components/AppShell.vue'

const route = useRoute()

/** Вход и настройка 2FA рисуются без боковой панели — идти по ней ещё некуда. */
const bare = computed(() => route.name === 'login' || route.name === 'totp-setup')
</script>

<template>
  <RouterView v-if="bare" />
  <AppShell v-else>
    <RouterView />
  </AppShell>
</template>
