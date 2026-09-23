package ru.marshruty.ar.ui

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke

/**
 * Значки управления, нарисованные вручную.
 *
 * Раньше здесь стояли символы Юникода — «✕», «⏸», «🔊». Android рисует их
 * шрифтом эмодзи: на телефоне кнопка паузы выходила ярко-оранжевым квадратом,
 * динамик — цветной картинкой, и весь ряд разъезжался по размеру, потому что
 * ширина эмодзи не совпадает с шириной обычного глифа. Свои фигуры дают
 * одинаковый размер, один цвет с остальным HUD и одинаковый вид на любом
 * телефоне, чем бы производитель ни подменил шрифт.
 */
internal enum class ArIcon { CLOSE, PLAY, PAUSE, REPLAY, FLIP, SOUND_ON, SOUND_OFF, TARGET }

@Composable
internal fun ArIconGlyph(
    icon: ArIcon,
    modifier: Modifier = Modifier,
    tint: Color = ArColors.SurfaceBright,
) {
    Canvas(modifier = modifier) {
        val stroke = size.minDimension * 0.1f
        when (icon) {
            ArIcon.CLOSE -> drawClose(tint, stroke)
            ArIcon.PLAY -> drawPlay(tint)
            ArIcon.PAUSE -> drawPause(tint)
            ArIcon.REPLAY -> drawReplay(tint, stroke)
            ArIcon.FLIP -> drawFlip(tint, stroke)
            ArIcon.SOUND_ON -> drawSound(tint, stroke, muted = false)
            ArIcon.SOUND_OFF -> drawSound(tint, stroke, muted = true)
            ArIcon.TARGET -> drawTarget(tint, stroke)
        }
    }
}

private fun DrawScope.drawClose(tint: Color, stroke: Float) {
    val pad = size.minDimension * 0.28f
    drawLine(tint, Offset(pad, pad), Offset(size.width - pad, size.height - pad), stroke, StrokeCap.Round)
    drawLine(tint, Offset(size.width - pad, pad), Offset(pad, size.height - pad), stroke, StrokeCap.Round)
}

private fun DrawScope.drawPlay(tint: Color) {
    val pad = size.minDimension * 0.28f
    // Чуть правее центра: треугольник «тяжелее» слева, и по геометрическому
    // центру он выглядит сдвинутым к краю.
    val path = Path().apply {
        moveTo(pad * 1.15f, pad)
        lineTo(size.width - pad * 0.85f, size.height / 2f)
        lineTo(pad * 1.15f, size.height - pad)
        close()
    }
    drawPath(path, tint)
}

private fun DrawScope.drawPause(tint: Color) {
    val pad = size.minDimension * 0.3f
    val barWidth = size.minDimension * 0.13f
    val height = size.height - pad * 2
    drawRect(tint, Offset(size.width / 2f - barWidth * 1.7f, pad), Size(barWidth, height))
    drawRect(tint, Offset(size.width / 2f + barWidth * 0.7f, pad), Size(barWidth, height))
}

private fun DrawScope.drawReplay(tint: Color, stroke: Float) {
    val pad = size.minDimension * 0.26f
    val rect = Rect(Offset(pad, pad), Size(size.width - pad * 2, size.height - pad * 2))
    // Разрыв сверху справа, в него смотрит наконечник — привычная стрелка «заново».
    drawArc(
        color = tint,
        startAngle = -50f,
        sweepAngle = 300f,
        useCenter = false,
        topLeft = rect.topLeft,
        size = rect.size,
        style = Stroke(width = stroke, cap = StrokeCap.Round),
    )
    val tip = Offset(rect.right - rect.width * 0.08f, rect.top + rect.height * 0.16f)
    val head = size.minDimension * 0.16f
    val arrow = Path().apply {
        moveTo(tip.x, tip.y)
        lineTo(tip.x - head, tip.y - head * 0.2f)
        lineTo(tip.x - head * 0.2f, tip.y + head)
        close()
    }
    drawPath(arrow, tint)
}

private fun DrawScope.drawFlip(tint: Color, stroke: Float) {
    // Оборот через голову: кольцо с наконечником, показывающим направление.
    // Без наконечника фигура читалась просто как незамкнутый кружок.
    val pad = size.minDimension * 0.22f
    val rect = Rect(Offset(pad, pad), Size(size.width - pad * 2, size.height - pad * 2))
    drawArc(
        color = tint,
        startAngle = 125f,
        sweepAngle = 290f,
        useCenter = false,
        topLeft = rect.topLeft,
        size = rect.size,
        style = Stroke(width = stroke, cap = StrokeCap.Round),
    )
    // Конец дуги — внизу слева, туда же смотрит и стрелка.
    val tip = Offset(rect.left + rect.width * 0.20f, rect.bottom - rect.height * 0.06f)
    val head = size.minDimension * 0.17f
    val arrow = Path().apply {
        moveTo(tip.x, tip.y)
        lineTo(tip.x - head * 0.15f, tip.y - head)
        lineTo(tip.x + head, tip.y - head * 0.45f)
        close()
    }
    drawPath(arrow, tint)
}

private fun DrawScope.drawSound(tint: Color, stroke: Float, muted: Boolean) {
    val pad = size.minDimension * 0.26f
    val bodyLeft = pad * 0.9f
    val coneRight = size.width * 0.46f
    val mid = size.height / 2f
    // Корпус динамика: прямоугольник у оси и раструб конусом.
    val speaker = Path().apply {
        moveTo(bodyLeft, mid - size.height * 0.1f)
        lineTo(size.width * 0.28f, mid - size.height * 0.1f)
        lineTo(coneRight, pad * 0.8f)
        lineTo(coneRight, size.height - pad * 0.8f)
        lineTo(size.width * 0.28f, mid + size.height * 0.1f)
        lineTo(bodyLeft, mid + size.height * 0.1f)
        close()
    }
    drawPath(speaker, tint)

    if (muted) {
        val from = Offset(size.width * 0.58f, mid - size.height * 0.16f)
        val to = Offset(size.width * 0.82f, mid + size.height * 0.16f)
        drawLine(tint, from, Offset(to.x, to.y), stroke, StrokeCap.Round)
        drawLine(tint, Offset(to.x, from.y), Offset(from.x, to.y), stroke, StrokeCap.Round)
    } else {
        // Две дуги звука — ближняя и дальняя.
        listOf(0.30f to 0.62f, 0.46f to 0.86f).forEach { (radiusFactor, _) ->
            val radius = size.minDimension * radiusFactor
            drawArc(
                color = tint,
                startAngle = -55f,
                sweepAngle = 110f,
                useCenter = false,
                topLeft = Offset(size.width * 0.34f - radius, mid - radius),
                size = Size(radius * 2, radius * 2),
                style = Stroke(width = stroke * 0.85f, cap = StrokeCap.Round),
            )
        }
    }
}

private fun DrawScope.drawTarget(tint: Color, stroke: Float) {
    val radius = size.minDimension * 0.28f
    val center = Offset(size.width / 2f, size.height / 2f)
    drawCircle(tint, radius, center, style = Stroke(width = stroke))
    drawCircle(tint, radius * 0.18f, center)
    val arm = size.minDimension * 0.14f
    listOf(
        Offset(center.x, center.y - radius - arm) to Offset(center.x, center.y - radius + arm * 0.2f),
        Offset(center.x, center.y + radius - arm * 0.2f) to Offset(center.x, center.y + radius + arm),
        Offset(center.x - radius - arm, center.y) to Offset(center.x - radius + arm * 0.2f, center.y),
        Offset(center.x + radius - arm * 0.2f, center.y) to Offset(center.x + radius + arm, center.y),
    ).forEach { (from, to) -> drawLine(tint, from, to, stroke, StrokeCap.Round) }
}
