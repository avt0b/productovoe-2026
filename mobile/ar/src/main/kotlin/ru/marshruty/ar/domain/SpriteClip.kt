package ru.marshruty.ar.domain

/** Что сейчас делает проводник. */
enum class CompanionAction {
    /** Стоит и дышит — состояние по умолчанию. */
    IDLE,

    /** Говорит: играет, пока звучит реплика. */
    TALKING,

    /** Трюк по кнопке: проигрывается один раз и возвращает к IDLE. */
    TRICK,
}

/**
 * Покадровая анимация персонажа.
 *
 * Кадры, а не 3D: персонаж приклеен к нижней трети экрана и камера вокруг него
 * не ходит, поэтому заранее отрисованная последовательность выглядит так же,
 * как реалтайм-рендер, но не тянет за собой Filament и работает везде.
 */
data class SpriteClip(
    val frameCount: Int,
    val fps: Int = 12,
    val loop: Boolean = true,
) {
    init {
        require(frameCount > 0) { "В клипе должен быть хотя бы один кадр" }
        require(fps in 1..120) { "Частота кадров вне разумного диапазона" }
    }

    /**
     * Длительность клипа, мс. Для петлевого — длительность одного круга.
     *
     * Деление с округлением вверх, а не нацело: 8 кадров при 12 к/с длятся
     * 666.67 мс, и при усечении до 666 мс последний кадр ещё не закончился —
     * петля не замыкалась, а непетлевой клип считался доигранным раньше срока.
     */
    val durationMillis: Long get() = (frameCount * 1000L + fps - 1) / fps

    /**
     * Кадр на заданный момент от начала клипа.
     *
     * `null` означает, что непетлевой клип доигран — вызывающий возвращает
     * персонажа в исходное состояние.
     */
    fun frameAt(elapsedMillis: Long): Int? {
        if (elapsedMillis < 0) return 0
        val raw = (elapsedMillis * fps / 1000L).toInt()
        return when {
            raw < frameCount -> raw
            loop -> raw % frameCount
            else -> null
        }
    }

    /** Доигран ли непетлевой клип. */
    fun isFinished(elapsedMillis: Long): Boolean = !loop && frameAt(elapsedMillis) == null

    companion object {
        /**
         * Тайминг сальто, когда кадров трюка нет.
         *
         * 0.9 секунды — столько длится прыжок с оборотом у живого человека;
         * быстрее читается как рывок, медленнее — как зависание в воздухе.
         */
        val DefaultTrick = SpriteClip(frameCount = 54, fps = 60, loop = false)
    }
}

/**
 * Какое действие показывать, исходя из состояния экрана.
 *
 * Трюк главнее речи: если пользователь нажал кнопку, он ждёт трюк, а не
 * продолжения рассказа.
 */
fun resolveCompanionAction(
    trickElapsedMillis: Long?,
    trickClip: SpriteClip?,
    isSpeaking: Boolean,
): CompanionAction = when {
    trickElapsedMillis != null && trickClip != null && !trickClip.isFinished(trickElapsedMillis) ->
        CompanionAction.TRICK
    isSpeaking -> CompanionAction.TALKING
    else -> CompanionAction.IDLE
}
