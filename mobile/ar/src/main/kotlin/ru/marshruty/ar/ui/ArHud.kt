package ru.marshruty.ar.ui

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import ru.marshruty.ar.domain.DeviceOrientation
import kotlin.math.roundToInt

/** Полоса прогресса сюжета вверху экрана. */
@Composable
internal fun StoryProgressBar(progress: Float, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(4.dp)
            .clip(CircleShape)
            .background(ArColors.SurfaceBright.copy(alpha = 0.25f)),
    ) {
        Box(
            Modifier
                .fillMaxWidth(progress.coerceIn(0f, 1f))
                .fillMaxHeight()
                .clip(CircleShape)
                .background(ArColors.TertiaryFixed),
        )
    }
}

/** Круглая кнопка поверх кадра: закрыть, звук. */
@Composable
internal fun HudIconButton(
    glyph: String,
    contentDescription: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    tint: Color = ArColors.SurfaceBright,
) {
    Box(
        modifier = modifier
            .size(44.dp) // тап-таргет не меньше 44dp: экраном пользуются на ходу
            .clip(CircleShape)
            .background(ArColors.InverseSurface.copy(alpha = 0.6f))
            .clickable(onClick = onClick)
            .semantics { this.contentDescription = contentDescription },
        contentAlignment = Alignment.Center,
    ) {
        Text(glyph, style = ArType.HeadlineSm, color = tint)
    }
}

/** Чип «Точка 2 из 4 · Рубеж связистов». */
@Composable
internal fun StepChip(stepIndex: Int, stepTotal: Int, title: String, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(999.dp))
            .background(ArColors.InverseSurface.copy(alpha = 0.75f))
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        PulsingDot(color = ArColors.Tertiary, size = 8.dp)
        Text(
            text = "Точка $stepIndex из $stepTotal · $title",
            style = ArType.LabelArchiveCode,
            color = ArColors.SurfaceBright,
        )
    }
}

/** Строка компаса: азимут и угол наклона. */
@Composable
internal fun CompassStrip(orientation: DeviceOrientation, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text = "AZ %03d° %s".format(orientation.azimuthDegrees.roundToInt() % 360, cardinal(orientation.azimuthDegrees)),
            style = ArType.LabelArchiveCode,
            color = ArColors.SurfaceBright.copy(alpha = 0.7f),
        )
        Box(
            Modifier
                .height(2.dp)
                .fillMaxWidth(0.35f)
                .clip(CircleShape)
                .background(ArColors.SurfaceBright.copy(alpha = 0.3f)),
        )
        Text(
            text = "ELEV %+.1f°".format(orientation.pitchDegrees),
            style = ArType.LabelArchiveCode,
            color = ArColors.SurfaceBright.copy(alpha = 0.7f),
        )
    }
}

/** Румб по азимуту — привычнее, чем голые градусы. */
internal fun cardinal(azimuthDegrees: Double): String {
    val names = listOf("С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ")
    val index = (((azimuthDegrees % 360.0) + 360.0) % 360.0 / 45.0).roundToInt() % 8
    return names[index]
}

/** Едва заметное перекрестие в центре кадра — «прицел» архивного видоискателя. */
@Composable
internal fun ViewfinderReticle(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier.fillMaxSize()) {
        val cx = size.width / 2f
        val cy = size.height / 2f
        val arm = size.minDimension * 0.18f
        val faint = ArColors.SurfaceBright.copy(alpha = 0.22f)

        drawLine(faint, Offset(cx - arm, cy), Offset(cx + arm, cy), strokeWidth = 1.5f)
        drawLine(faint, Offset(cx, cy - arm), Offset(cx, cy + arm), strokeWidth = 1.5f)
        drawCircle(ArColors.SurfaceBright.copy(alpha = 0.4f), radius = 3f, center = Offset(cx, cy))
    }
}

/** Затемнение сверху и снизу, чтобы белый текст читался на любом кадре. */
@Composable
internal fun EdgeScrim(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    0.0f to ArColors.InverseSurface.copy(alpha = 0.55f),
                    0.35f to Color.Transparent,
                    0.6f to Color.Transparent,
                    1.0f to ArColors.InverseSurface.copy(alpha = 0.85f),
                ),
            ),
    )
}

/** Пульсирующая точка-индикатор. */
@Composable
internal fun PulsingDot(color: Color, size: androidx.compose.ui.unit.Dp, modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "dot")
    val alpha by transition.animateFloat(
        initialValue = 0.35f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(900), RepeatMode.Reverse),
        label = "dotAlpha",
    )
    Box(
        modifier
            .size(size)
            .clip(CircleShape)
            .background(color.copy(alpha = alpha)),
    )
}

/** Всплывающая плашка подтверждения находки. */
@Composable
internal fun DiscoveryToast(text: String, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(999.dp))
            .background(ArColors.Primary)
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("✓", style = ArType.LabelAction, color = ArColors.PrimaryFixed)
        Text(text, style = ArType.LabelArchiveCode, color = ArColors.OnPrimary, textAlign = TextAlign.Start)
    }
}

/** Плашка «гео недостоверно» — вместо метки, которая соврёт. */
@Composable
internal fun UnreliableLocationNotice(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(ArColors.InverseSurface.copy(alpha = 0.85f))
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Text("СИГНАЛ GPS СЛАБЫЙ", style = ArType.LabelArchiveCode, color = ArColors.TertiaryFixedDim)
        Text(
            "Метку не показываем, чтобы не увести в сторону. Выйдите на открытое место.",
            style = ArType.BodySm,
            color = ArColors.InverseOnSurface,
        )
    }
}
