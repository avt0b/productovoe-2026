<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { updateMyProfile } from '@modules/profile'
import { useAuthSession } from './session.js'
import AuthField from './components/AuthField.vue'
import SsoButtons from './components/SsoButtons.vue'

const router = useRouter()
const { session, login, register } = useAuthSession()

/** 'login' | 'register' */
const mode = ref('login')
const name = ref('')
const contact = ref('')
const password = ref('')
const passwordVisible = ref(false)
const signInError = ref('')
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

/** Вход по почте и регистрация. Удачный исход ведёт в профиль исследователя. */
async function submit() {
  if (submitting.value) return
  signInError.value = ''
  if (!contact.value || !password.value) {
    signInError.value = 'Заполните почту и пароль'
    return
  }
  if (mode.value === 'register' && password.value.length < 8) {
    signInError.value = 'Пароль должен быть не короче 8 символов'
    return
  }
  submitting.value = true
  try {
    if (mode.value === 'login') {
      await login({ email: contact.value, password: password.value })
    } else {
      // Роль по умолчанию: краеведом или наставником человека отмечают в
      // профиле, на экране регистрации выбора роли нет.
      await register({ email: contact.value, password: password.value, role: 'family' })
      // Имя хранится не там же, где логин с паролем, поэтому отдельным
      // запросом сразу после того, как появился access-токен. Если это
      // упадёт — регистрацию не откатываем, имя дозаполнится в профиле.
      if (name.value.trim()) {
        try {
          await updateMyProfile(session.accessToken, { display_name: name.value.trim() })
        } catch {
          // best-effort — аккаунт уже создан
        }
      }
    }
    router.push('/profile')
  } catch (err) {
    signInError.value = err.detail ?? 'Не удалось войти. Проверьте почту и пароль'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <!--
    Экран входа — один и тот же в вебе и в мобильном приложении
    (`frontend/client/src/modules/auth/AuthPage.vue`). Правки по вёрстке
    вносим в оба места, иначе экраны разъедутся снова.
  -->
  <div class="auth-flame relative isolate flex min-h-screen w-full flex-col items-center overflow-hidden px-margin py-space-lg">
    <!--
      Фотография вечного огня во весь экран. Лежит локально в `public/`, а не
      внешней ссылкой. Поверх — затемнение, без него белый текст на пламени
      не прочитать.
    -->
    <div class="pointer-events-none absolute inset-0 -z-10" aria-hidden="true">
      <img src="/auth-eternal-flame.jpg" alt="" class="h-full w-full object-cover" />
      <div class="absolute inset-0 bg-night/45" />
      <!-- Снизу тень гуще: там лежат мелкий текст и кнопки входа через сервисы -->
      <div class="absolute inset-0 bg-gradient-to-b from-night/20 via-transparent to-night/70" />
    </div>

    <!-- Колонка шириной телефона: на широком экране форма не растягивается -->
    <div class="my-auto flex w-full max-w-app flex-col">
      <header class="mb-space-md flex flex-col items-center text-center">
        <h1 class="ribbon-shimmer font-headline-xl text-headline-xl tracking-tight text-white drop-shadow-lg">
          Маршруты победы
        </h1>
        <p
          class="ribbon-shimmer mt-space-xs max-w-[32ch] font-body-md text-body-md text-white opacity-75 [animation-delay:700ms]"
        >
          Живая история, семейные маршруты и поиск защитников Отечества
        </p>
      </header>

      <!-- Стеклянная карточка: держит форму читаемой поверх фотографии -->
      <div
        class="flex w-full flex-col rounded-2xl border border-white/15 bg-night/45 p-space-md shadow-sheet backdrop-blur-md"
      >
        <!--
          Вход / Регистрация. Подложка активной вкладки — отдельный элемент,
          который переезжает трансформацией: перекраска фона у двух кнопок
          переключалась бы рывком, здесь же видно, куда именно уехал выбор.
        -->
        <div
          class="relative mb-space-md grid grid-cols-2 rounded-xl border border-white/10 bg-white/10 p-1 text-center"
          role="tablist"
        >
          <span
            class="absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-lg bg-white shadow-float transition-transform duration-300 ease-out"
            :class="mode === 'register' ? 'translate-x-full' : 'translate-x-0'"
            aria-hidden="true"
          />
          <button
            v-for="tab in [
              { value: 'login', title: 'Вход' },
              { value: 'register', title: 'Регистрация' },
            ]"
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
          <!--
            Графа имени не снимается с разметки, а схлопывается: высота едет
            через `grid-template-rows: 0fr → 1fr` обычным CSS-переходом.
            Скрытая графа помечена `inert` — в неё не попасть ни табом, ни
            скринридером.
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
                <span class="material-symbols-outlined text-[18px]" aria-hidden="true">
                  {{ passwordVisible ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </template>
          </AuthField>

          <button
            type="submit"
            class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70"
            :disabled="submitting"
          >
            <span
              class="material-symbols-outlined text-[18px]"
              :class="{ 'animate-spin': submitting }"
              aria-hidden="true"
            >
              {{ submitting ? 'progress_activity' : 'military_tech' }}
            </span>
            <span class="ribbon-shimmer [animation-delay:1400ms]">{{ submitLabel }}</span>
          </button>

          <!--
            Плашка ошибки не появляется рывком, а раскрывается высотой
            (`grid-template-rows: 0fr → 1fr`): иначе карточка при первой же
            ошибке подпрыгивала. Скрытая графа помечена `inert` — её не читает
            скринридер и не берёт таб.
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
        </form>

        <div class="relative flex items-center justify-center py-space-sm">
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
  </div>
</template>

<style>
/*
 * Автозаполнение. Chrome закрашивает поле с сохранённым паролем своим белым
 * фоном и тёмным текстом — на тёмной форме поверх фотографии это выглядит как
 * две белые плашки. Сам фон стилями не снимается: он рисуется поверх, и
 * `background-color` его не перебивает. Работает единственный приём — отложить
 * переход фона на срок, до которого дело не дойдёт, и отдельно задать цвет
 * текста и каретки. Правило привязано к `.auth-flame`: на светлых формах
 * остальных экранов белый текст автозаполнения пропал бы на белом фоне.
 */
.auth-flame input:-webkit-autofill,
.auth-flame input:-webkit-autofill:hover,
.auth-flame input:-webkit-autofill:focus,
.auth-flame input:-webkit-autofill:active {
  -webkit-text-fill-color: #ffffff;
  caret-color: #ffffff;
  transition: background-color 100000s ease-in-out 0s;
}
</style>
