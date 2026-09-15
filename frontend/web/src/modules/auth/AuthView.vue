<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AuthTabs from './components/AuthTabs.vue'
import LoginForm from './components/LoginForm.vue'
import RegisterForm from './components/RegisterForm.vue'
import SocialLogin from './components/SocialLogin.vue'

const mode = ref('login')
const router = useRouter()
const bgVideoFailed = ref(false)

function onSuccess() {
  setTimeout(() => router.push('/profile'), 600)
}
</script>

<template>
  <div class="min-h-screen w-full flex items-center justify-center p-6 relative overflow-hidden bg-secondary">
    <video
      v-if="!bgVideoFailed"
      class="absolute inset-0 w-full h-full object-cover"
      src="/video/victory-bg.mp4"
      autoplay
      muted
      loop
      playsinline
      @error="bgVideoFailed = true"
    />
    <div class="absolute inset-0 bg-secondary/80" />
    <div class="absolute -left-24 -top-24 w-96 h-96 rounded-full bg-secondary-fixed/10 blur-3xl pointer-events-none" />
    <div class="absolute right-1/4 -bottom-24 w-80 h-80 rounded-full bg-primary/10 blur-2xl pointer-events-none" />

    <div class="w-full max-w-md bg-surface-container-lowest rounded-lg shadow-xl p-8 flex flex-col gap-6 relative z-10">
      <div class="flex flex-col items-center gap-2 text-center">
        <div class="w-14 h-14 rounded-full bg-primary flex items-center justify-center shadow-md">
          <span class="material-symbols-outlined text-on-primary text-[28px]" style="font-variation-settings: 'FILL' 1">
            military_tech
          </span>
        </div>
        <span class="font-headline-sm text-headline-sm text-on-surface font-bold tracking-tight">Маршруты победы</span>
        <span class="font-label-sm text-label-sm text-secondary uppercase tracking-wider">Архивно-полевой центр</span>
      </div>

      <AuthTabs v-model="mode" />

      <LoginForm v-if="mode === 'login'" @success="onSuccess" />
      <RegisterForm v-else @success="onSuccess" />

      <SocialLogin @success="onSuccess" />

      <p class="text-center font-body-sm text-body-sm text-on-surface-variant">
        {{ mode === 'login' ? 'Нет аккаунта?' : 'Уже есть аккаунт?' }}
        <button
          class="text-primary font-bold hover:underline"
          @click="mode = mode === 'login' ? 'register' : 'login'"
        >
          {{ mode === 'login' ? 'Зарегистрироваться' : 'Войти' }}
        </button>
      </p>
    </div>
  </div>
</template>
