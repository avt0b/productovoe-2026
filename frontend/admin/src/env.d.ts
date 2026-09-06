/// <reference types="vite/client" />

// Шима для *.vue здесь намеренно нет: vue-tsc разбирает SFC сам, а ручная
// декларация превратила бы все компоненты в `any` и убила проверку пропсов.

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
}
