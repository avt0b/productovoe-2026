/**
 * Токены «Маршруты победы».
 *
 * Основа — экспорт Google Stitch (схема Material 3: пары `primary`/`on-primary`,
 * `surface`/`on-surface`). Поверх неё — архивная тема: вместо холодного серого
 * интерфейса лист старого пергамента, акцент — цвета георгиевской ленты.
 * Новые цвета сюда, а не в компоненты: произвольных `#hex` в разметке быть не должно.
 */

const manrope = ['Manrope', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif']

/**
 * Пергамент: лист, на котором лежит всё приложение. От самого светлого
 * (карточка поверх листа) к самому тёмному (штриховка, разделители).
 */
const parchment = {
  lightest: '#fdf8ec',
  lighter: '#f8f0dd',
  base: '#f3e9d2',
  dim: '#ecdfc2',
  deep: '#e3d3ae',
  shade: '#d6c295',
  line: '#c2ab7c',
}

/**
 * Охра и чёрный георгиевской ленты. Самой ленты на экранах уже нет,
 * но из этих цветов собрана третичная роль — «наградные» акценты.
 */
const ribbon = {
  black: '#241f18',
  'black-soft': '#3a3227',
  orange: '#e8a33d',
  'orange-deep': '#c97f1c',
  'orange-pale': '#f6dcae',
}

/**
 * Ночной слой: экран входа лежит на фотографии, и поверх неё нужен
 * затемняющий подмалёвок плюс стеклянные поверхности формы.
 */
const night = {
  DEFAULT: '#0d0b09',
  soft: '#1d1815',
}

/** Выцветшие чернила — текст и штампы на пергаменте. */
const ink = {
  DEFAULT: '#2c2519',
  muted: '#6a5c44',
  faded: '#9a886a',
}

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      screens: {
        /**
         * Низкий экран (iPhone SE, старые Android). Вёрстка входа на нём
         * ужимается, чтобы форма целиком помещалась без прокрутки.
         */
        short: { raw: '(max-height: 740px)' },
      },
      colors: {
        parchment,
        ink,
        night,

        background: parchment.base,
        surface: parchment.base,
        'surface-bright': parchment.lighter,
        'surface-dim': parchment.deep,
        'surface-tint': '#ae3024',
        'surface-variant': parchment.dim,
        'surface-container-lowest': parchment.lightest,
        'surface-container-low': parchment.lighter,
        'surface-container': parchment.dim,
        'surface-container-high': parchment.deep,
        'surface-container-highest': parchment.shade,
        'inverse-surface': ink.DEFAULT,
        'inverse-on-surface': parchment.lightest,

        primary: '#a52a1f',
        'primary-container': '#c23c2b',
        'on-primary': '#fdf8ec',
        'on-primary-container': '#fffbff',
        'primary-fixed': '#f6d9cf',
        'primary-fixed-dim': '#e8a999',
        'on-primary-fixed': '#3d0c06',
        'on-primary-fixed-variant': '#7e1d14',
        'inverse-primary': '#e8a999',

        secondary: '#4d5e43',
        'secondary-container': '#d8e0c8',
        'on-secondary': '#fdf8ec',
        'on-secondary-container': '#3c4a35',
        'secondary-fixed': '#dde5cd',
        'secondary-fixed-dim': '#bcc9ae',
        'on-secondary-fixed': '#141d0f',
        'on-secondary-fixed-variant': '#39472f',

        // Третичный — латунь и охра: награды, отличия, «наградные» акценты.
        tertiary: '#8a5a13',
        'tertiary-container': ribbon['orange-deep'],
        'on-tertiary': '#fdf8ec',
        'on-tertiary-container': '#fffbff',
        'tertiary-fixed': ribbon['orange-pale'],
        'tertiary-fixed-dim': ribbon.orange,
        'on-tertiary-fixed': '#2c1a00',
        'on-tertiary-fixed-variant': '#6b4200',

        error: '#a51b14',
        'error-container': '#f5d7ce',
        'on-error': '#fdf8ec',
        'on-error-container': '#7a0d09',

        'on-surface': ink.DEFAULT,
        'on-surface-variant': ink.muted,
        'on-background': ink.DEFAULT,
        outline: ink.faded,
        'outline-variant': parchment.line,

        // Цвета, которые в макете стояли прямо в разметке. Вынесены сюда,
        // чтобы у каждого было имя и одно место правки.
        /** «Полевая школа» на экране «Штаб»: оливковая карточка выезда. */
        field: {
          DEFAULT: '#4d5e43',
          muted: '#5b6e58',
          line: '#7a8d77',
          surface: '#eef0e4',
          'surface-high': '#e6eada',
        },
        /** Нарисованная карта маршрутов: бумага, сетка, лес, река. */
        map: {
          paper: parchment.lighter,
          grid: parchment.deep,
          forest: '#dfe5d3',
          river: '#bcd3cc',
        },
        /** Подложка «Задания исследователя». */
        quest: parchment.lightest,
      },
      borderRadius: {
        // Шкала крупная: `xl` здесь 3rem, а не привычные 0.75rem. На невысоком
        // элементе такое скругление съедает верхние и нижние углы целиком, и
        // кнопка превращается в овал — для карточек берите `2xl` (1rem).
        DEFAULT: '1rem',
        lg: '2rem',
        xl: '3rem',
        full: '9999px',
        /** Нижняя панель, плеер портрета, выезжающая карточка маршрута. */
        sheet: '28px',
      },
      boxShadow: {
        // Тени тёплые: на пергаменте серая тень выглядит грязным пятном.
        header: '0 1px 8px rgba(92, 69, 32, 0.07)',
        nav: '0 10px 25px -5px rgba(92, 69, 32, 0.12)',
        sheet: '0 12px 36px rgba(92, 69, 32, 0.13)',
        float: '0 4px 16px rgba(92, 69, 32, 0.12)',
        /** Карточка-документ, лежащая на листе: мягкая тень плюс тёплый кант. */
        document: '0 2px 0 rgba(255, 252, 242, 0.7) inset, 0 8px 24px rgba(92, 69, 32, 0.12)',
        /** Оттиск печати и наградных кнопок. */
        stamp: '0 2px 10px rgba(122, 29, 20, 0.28)',
      },
      spacing: {
        'space-xs': '0.25rem',
        'space-sm': '0.5rem',
        'space-md': '1rem',
        'space-lg': '1.5rem',
        'space-xl': '2rem',
        'space-2xl': '3rem',
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
        /** Архивная надпись: разрядка вразбивку, как на описи дела. */
        archival: manrope,
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
        /** Надзаголовки-рубрики: «ЭКСПЕДИЦИЯ ПАМЯТИ», «АРХИВ». */
        archival: ['11px', { lineHeight: '14px', letterSpacing: '0.18em', fontWeight: '700' }],
      },
      maxWidth: {
        /** Ширина «телефона»: на десктопе приложение не растягивается во весь экран. */
        app: '480px',
      },
    },
  },
  plugins: [],
}
