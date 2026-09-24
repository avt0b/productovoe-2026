<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorText } from '@/core/format'
import { useSessionStore } from '@/core/session'
import MsIcon from '@/ui/MsIcon.vue'

import AuthField from './components/AuthField.vue'
import SsoButtons from './components/SsoButtons.vue'

type Mode = 'login' | 'register'

const route = useRoute()
const router = useRouter()
const session = useSessionStore()

const mode = ref<Mode>('login')
const name = ref('')
const contact = ref('')
const password = ref('')
const passwordVisible = ref(false)
const signInError = ref<string | null>(null)
/**
 * Текст последней ошибки. Плашка не снимается с разметки, а схлопывается, и
 * пока идёт анимация, текст ещё нужен: с `signInError` внутри плашка на
 * полсекунды становилась пустой красной полосой.
 */
const lastError = ref('')
watch(signInError, (value) => {
  if (value) lastError.value = value
})
const submitting = ref(false)

const submitLabel = computed(() => (mode.value === 'login' ? 'Войти в экспедицию' : 'Создать аккаунт'))

/**
 * Куда вернуть после входа. Только внутренний путь: `?next=//evil.example`
 * иначе увёл бы человека на чужой сайт прямо с экрана входа.
 */
function nextPath(): string | null {
  const next = route.query.next
  return typeof next === 'string' && next.startsWith('/') && !next.startsWith('//') ? next : null
}

/** Вход по почте и регистрация. Удачный исход ведёт в профиль исследователя. */
async function submit(): Promise<void> {
  if (submitting.value) return
  submitting.value = true
  signInError.value = null
  try {
    await session.signIn({
      method: mode.value === 'login' ? 'password' : 'register',
      contact: contact.value,
      password: password.value,
      name: mode.value === 'register' ? name.value : undefined,
    })
    await router.replace(nextPath() ?? { name: 'home' })
  } catch (reason) {
    signInError.value = errorText(reason)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <!--
    Контент прижат к верху, а не центрирован. При переключении «Вход» ⇄
    «Регистрация» форма становится на поле выше, и при центрировании весь
    экран, включая шапку и вкладки, дёргался бы вверх-вниз. Сверху же
    неподвижно стоит всё до нового поля, а ниже него блок плавно съезжает.
  -->
  <div
    class="relative isolate flex w-full flex-1 flex-col overflow-hidden px-margin pb-space-sm short:pb-space-xs"
  >
    <!--
      Фотография вечного огня во весь экран. Лежит локально в `public/`:
      в APK сети может не быть, и внешняя картинка там просто не загрузится.
      Поверх — затемнение, без него белый текст на пламени не прочитать.
    -->
    <div class="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <img src="/auth-eternal-flame.jpg" alt="" class="h-full w-full object-cover" />
      <div class="absolute inset-0 bg-night/45" />
      <!-- Снизу тень гуще: там лежат мелкий текст и кнопки входа через сервисы -->
      <div class="absolute inset-0 bg-gradient-to-b from-night/20 via-transparent to-night/70" />
    </div>

    <header class="mb-space-sm mt-space-2xl flex flex-col items-center text-center short:mb-space-xs short:mt-space-md">
      <h1
        class="ribbon-shimmer font-headline-xl text-headline-xl tracking-tight text-white drop-shadow-lg short:text-headline-xl-mobile"
      >
        Маршруты победы
      </h1>
      <p
        class="ribbon-shimmer mt-space-xs max-w-[32ch] font-body-md text-body-md text-white opacity-75 [animation-delay:700ms] short:text-body-sm"
      >
        Живая история, семейные маршруты и поиск защитников Отечества
      </p>
    </header>

    <!--
      Стеклянная карточка: держит форму читаемой поверх фотографии.
      `mt-auto` работает только когда маскот скрыт (низкий экран) — тогда
      форма всё равно остаётся у нижнего края, а не взлетает под шапку.
    -->
    <div
      class="mt-auto flex w-full flex-col rounded-2xl border border-white/15 bg-night/45 p-space-md shadow-sheet backdrop-blur-md"
    >
      <!--
        Вход / Регистрация. Подложка активной вкладки — отдельный элемент,
        который переезжает трансформацией: перекраска фона у двух кнопок
        переключалась бы рывком, здесь же видно, куда именно уехал выбор.
      -->
      <div class="relative mb-space-md grid grid-cols-2 rounded-xl border border-white/10 bg-white/10 p-1 text-center" role="tablist">
        <span
          class="absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-lg bg-white shadow-float transition-transform duration-300 ease-out"
          :class="mode === 'register' ? 'translate-x-full' : 'translate-x-0'"
          aria-hidden="true"
        />
        <button
          v-for="tab in [
            { value: 'login', title: 'Вход' },
            { value: 'register', title: 'Регистрация' },
          ] as const"
          :key="tab.value"
          type="button"
          role="tab"
          :aria-selected="mode === tab.value"
          class="relative z-10 rounded-lg py-2 font-label-lg text-label-lg transition-colors duration-200"
          :class="mode === tab.value ? 'text-night' : 'text-white/70 hover:text-white'"
          @click="mode = tab.value"
        >
          {{ tab.title }}
        </button>
      </div>

      <form class="flex flex-col" @submit.prevent="submit">
        <!-- Обёртка-грид нужна анимации высоты: см. `.field-*` в style.css -->
        <!--
          Графа имени не снимается с разметки, а схлопывается: высота едет
          через `grid-template-rows: 0fr → 1fr` обычным CSS-переходом. С
          `<Transition>` элемент снимался по событию анимации и залипал
          раскрытым, если окно в этот момент не отрисовывалось. Скрытая графа
          помечена `inert` — в неё не попасть ни табом, ни скринридером.
        -->
        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="mode === 'register' ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          :inert="mode !== 'register'"
        >
          <div class="overflow-hidden">
            <AuthField
              v-model="name"
              class="mb-space-sm"
              label="Как к вам обращаться"
              icon="person"
              placeholder="Имя и фамилия"
              autocomplete="name"
            />
          </div>
        </div>

        <AuthField
          v-model="contact"
          class="mb-space-sm"
          label="Почта"
          icon="mail"
          type="email"
          placeholder="name@mail.ru"
          autocomplete="username"
        />

        <AuthField
          v-model="password"
          class="mb-space-md"
          label="Пароль"
          icon="lock"
          :type="passwordVisible ? 'text' : 'password'"
          :placeholder="mode === 'login' ? 'Введите ваш пароль' : 'Не короче 8 символов'"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
        >
          <template #trailing>
            <button
              type="button"
              class="flex shrink-0 items-center p-1 text-white/60 transition-colors hover:text-white"
              :aria-label="passwordVisible ? 'Скрыть пароль' : 'Показать пароль'"
              @click="passwordVisible = !passwordVisible"
            >
              <MsIcon :name="passwordVisible ? 'visibility_off' : 'visibility'" :size="18" />
            </button>
          </template>
        </AuthField>

        <button
          type="submit"
          class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
          :disabled="submitting"
        >
          <MsIcon
            :name="submitting ? 'progress_activity' : 'military_tech'"
            :size="18"
            :class="{ 'animate-spin': submitting }"
          />
          <span class="ribbon-shimmer [animation-delay:1400ms]">{{ submitLabel }}</span>
        </button>

        <!--
          Ошибка и подсказка про демо-режим стоят в одном месте: плашка встаёт
          вместо подсказки, а не над ней. Обе графы схлопываются высотой
          (`grid-template-rows: 0fr → 1fr`), поэтому при первой же ошибке
          карточка не дёргается вверх рывком и не выталкивает за край экрана
          строку про Политику памяти — разницу высот она проезжает плавно.
          Скрытая графа помечена `inert`: её не читает скринридер и не берёт таб.
        -->
        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="signInError ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          :inert="!signInError"
        >
          <div class="overflow-hidden">
            <p
              class="mt-space-sm rounded-xl bg-error/90 px-space-sm py-2 text-center font-body-sm text-body-sm text-white"
              role="alert"
            >
              {{ lastError }}
            </p>
          </div>
        </div>

        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="signInError ? 'grid-rows-[0fr] opacity-0' : 'grid-rows-[1fr] opacity-100'"
          :inert="signInError !== null"
        >
          <div class="overflow-hidden">
            <p class="mt-space-sm text-center font-label-sm text-label-sm text-white/75">
              Пустые поля — вход в демо-режиме: смотреть можно всё, записываться и отмечать — нет.
            </p>
          </div>
        </div>
      </form>

      <div class="relative flex items-center justify-center py-space-sm short:py-0.5">
        <div class="h-px flex-grow bg-white/20" />
        <span class="mx-space-sm shrink-0 font-archival text-archival uppercase text-white/70">Или войти через</span>
        <div class="h-px flex-grow bg-white/20" />
      </div>

      <SsoButtons />
    </div>

    <p class="mt-space-sm px-space-sm text-center font-label-sm text-label-sm text-white/75">
      Нажимая «Войти», вы соглашаетесь с
      <!-- Закон «Об увековечении памяти погибших при защите Отечества» на сайте Кремля -->
      <a
        class="underline transition-colors hover:text-white"
        href="http://www.kremlin.ru/acts/bank/7640"
        target="_blank"
        rel="noopener noreferrer"
        >Политикой памяти</a
      >
      и правилами обработки персональных данных.
    </p>
  </div>
</template>
