/**
 * Токены перенесены из экспорта Google Stitch без изменений — чтобы вёрстка
 * совпадала с макетом один в один. Новые цвета сюда, а не в компоненты:
 * произвольных `#hex` в разметке быть не должно.
 */

const manrope = ['Manrope', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif']

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        background: '#f9f9fb',
        surface: '#f9f9fb',
        'surface-bright': '#f9f9fb',
        'surface-dim': '#d9dadc',
        'surface-tint': '#ae3024',
        'surface-variant': '#e2e2e5',
        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#f3f3f6',
        'surface-container': '#eeeef0',
        'surface-container-high': '#e8e8ea',
        'surface-container-highest': '#e2e2e5',
        'inverse-surface': '#2f3133',
        'inverse-on-surface': '#f0f0f3',

        primary: '#ab2e22',
        'primary-container': '#cd4637',
        'on-primary': '#ffffff',
        'on-primary-container': '#fffbff',
        'primary-fixed': '#ffdad5',
        'primary-fixed-dim': '#ffb4a9',
        'on-primary-fixed': '#410000',
        'on-primary-fixed-variant': '#8c170f',
        'inverse-primary': '#ffb4a9',

        secondary: '#51634e',
        'secondary-container': '#d3e9cd',
        'on-secondary': '#ffffff',
        'on-secondary-container': '#566954',
        'secondary-fixed': '#d3e9cd',
        'secondary-fixed-dim': '#b7ccb2',
        'on-secondary-fixed': '#0f1f0f',
        'on-secondary-fixed-variant': '#394b37',

        tertiary: '#854f00',
        'tertiary-container': '#a76500',
        'on-tertiary': '#ffffff',
        'on-tertiary-container': '#fffbff',
        'tertiary-fixed': '#ffdcbc',
        'tertiary-fixed-dim': '#ffb86a',
        'on-tertiary-fixed': '#2c1700',
        'on-tertiary-fixed-variant': '#683d00',

        error: '#ba1a1a',
        'error-container': '#ffdad6',
        'on-error': '#ffffff',
        'on-error-container': '#93000a',

        'on-surface': '#1a1c1e',
        'on-surface-variant': '#59413d',
        'on-background': '#1a1c1e',
        outline: '#8d706c',
        'outline-variant': '#e1bfba',

        // Цвета, которые в макете стояли прямо в разметке. Вынесены сюда,
        // чтобы у каждого было имя и одно место правки.
        /** «Полевая школа» на экране «Штаб»: оливковая карточка выезда. */
        field: {
          DEFAULT: '#4d5e43',
          muted: '#5b6e58',
          line: '#7a8d77',
          surface: '#f2f5f0',
          'surface-high': '#ebf0e8',
        },
        /** Нарисованная карта маршрутов: бумага, сетка, лес, река. */
        map: {
          paper: '#f4f1ea',
          grid: '#dfe5dc',
          forest: '#e6ede4',
          river: '#b6d2d1',
        },
        /** Подложка «Задания исследователя». */
        quest: '#fdf6ed',
      },
      borderRadius: {
        DEFAULT: '1rem',
        lg: '2rem',
        xl: '3rem',
        full: '9999px',
        /** Нижняя панель, плеер портрета, выезжающая карточка маршрута. */
        sheet: '28px',
      },
      boxShadow: {
        header: '0 1px 8px rgba(0, 0, 0, 0.04)',
        nav: '0 10px 25px -5px rgba(36, 38, 40, 0.08)',
        sheet: '0 12px 36px rgba(36, 38, 40, 0.08)',
        float: '0 4px 16px rgba(36, 38, 40, 0.08)',
      },
      spacing: {
        'space-xs': '0.25rem',
        'space-sm': '0.5rem',
        'space-md': '1rem',
        'space-lg': '1.5rem',
        'space-xl': '2rem',
        margin: '1rem',
        'margin-tablet': '2rem',
        'margin-desktop': '3rem',
        gutter: '1rem',
        'gutter-tablet': '1.25rem',
        'gutter-desktop': '1.5rem',
        /** 52 px — круглые кнопки нижней панели карты. */
        13: '3.25rem',
      },
      fontFamily: {
        'headline-xl': manrope,
        'headline-xl-mobile': manrope,
        'headline-lg': manrope,
        'headline-lg-mobile': manrope,
        'headline-md': manrope,
        'headline-sm': manrope,
        'body-lg': manrope,
        'body-md': manrope,
        'body-sm': manrope,
        'label-lg': manrope,
        'label-md': manrope,
        'label-sm': manrope,
      },
      fontSize: {
        'headline-xl': ['40px', { lineHeight: '48px', letterSpacing: '-0.02em', fontWeight: '800' }],
        'headline-xl-mobile': ['30px', { lineHeight: '38px', letterSpacing: '-0.02em', fontWeight: '800' }],
        'headline-lg': ['28px', { lineHeight: '36px', letterSpacing: '-0.01em', fontWeight: '700' }],
        'headline-lg-mobile': ['24px', { lineHeight: '32px', letterSpacing: '-0.01em', fontWeight: '700' }],
        'headline-md': ['20px', { lineHeight: '28px', fontWeight: '700' }],
        'headline-sm': ['18px', { lineHeight: '26px', fontWeight: '600' }],
        'body-lg': ['17px', { lineHeight: '26px', fontWeight: '400' }],
        'body-md': ['15px', { lineHeight: '24px', fontWeight: '400' }],
        'body-sm': ['13px', { lineHeight: '20px', fontWeight: '400' }],
        'label-lg': ['15px', { lineHeight: '20px', letterSpacing: '0.01em', fontWeight: '600' }],
        'label-md': ['13px', { lineHeight: '18px', letterSpacing: '0.02em', fontWeight: '600' }],
        'label-sm': ['11px', { lineHeight: '16px', letterSpacing: '0.04em', fontWeight: '700' }],
      },
      maxWidth: {
        /** Ширина «телефона»: на десктопе приложение не растягивается во весь экран. */
        app: '480px',
      },
    },
  },
  plugins: [],
}
