/**
 * Вид поля ввода — один на все формы приложения.
 *
 * Поле — строка, а не коробка: рамка вокруг каждой графы превращает форму в
 * решётку, и на экране с картой или фотографией это особенно заметно. Остаётся
 * линия снизу, в фокусе она перекрашивается в кумач — видно, какую графу
 * заполняют. Тот же приём на экране входа (`modules/auth/components/AuthField.vue`),
 * только там линия белая по фотографии.
 */

/** Подпись над графой. */
export const FIELD_LABEL_CLASS = 'font-label-md text-label-md text-on-surface-variant'

/** Строка графы: иконка, поле и то, что стоит справа (кнопка, единица измерения). */
export const FIELD_LINE_CLASS =
  'flex items-center gap-space-sm border-b border-outline-variant py-2.5 transition-colors focus-within:border-primary'

/**
 * Само поле. Кольцо фокуса снято намеренно: фокус уже показывает линия снизу,
 * а глобальное `:focus-visible` обвело бы прозрачный инпут рамкой поверх неё.
 */
export const INPUT_CLASS =
  'min-w-0 flex-1 border-none bg-transparent font-body-md text-body-md text-on-surface outline-none placeholder:text-outline focus-visible:ring-0 focus-visible:ring-offset-0 disabled:opacity-60'

/** Многострочное поле остаётся коробкой: линия снизу у текста в три строки не читается как графа. */
export const TEXTAREA_CLASS =
  'w-full rounded-DEFAULT border border-outline-variant bg-surface-container-lowest/70 px-space-sm py-2 font-body-md text-body-md text-on-surface outline-none transition-colors placeholder:text-outline focus:border-primary focus-visible:ring-0 focus-visible:ring-offset-0 disabled:opacity-60'

/** Пояснение под графой. */
export const FIELD_HINT_CLASS = 'font-body-sm text-body-sm text-on-surface-variant'

