package ru.marshruty.ar.ui

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.unit.dp
import ru.marshruty.ar.domain.OffScreenHint
import ru.marshruty.ar.domain.ScreenPosition
import kotlin.math.roundToInt

/**
 * Метка цели в кадре.
 *
 * Позиция приходит долями кадра из [ScreenPosition] — вся геометрия посчитана
 * в домене и покрыта тестами, здесь только отрисовка.
 */
@Composable
internal fun TargetMarker(
    position: ScreenPosition,
    label: String,
    distanceMeters: Double?,
    coordinatesText: String?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    BoxWithConstraints(modifier = modifier.fillMaxSize()) {
        if (!position.onScreen) return@BoxWithConstraints

        val x = maxWidth * position.xFraction
        val y = maxHeight * position.yFraction

        Column(
            modifier = Modifier
                // Смещаем на половину размера метки, чтобы центр кружка попал в точку.
                .offset(x = x - 40.dp, y = y - 24.dp)
                .clickable(onClick = onClick),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            RadarPulse()

            if (coordinatesText != null) {
                Text(
                    text = coordinatesText,
                    style = ArType.LabelCoordinate,
                    color = ArColors.InverseOnSurface,
                    modifier = Modifier
                        .clip(RoundedCornerShape(999.dp))
                        .background(ArColors.InverseSurface.copy(alpha = 0.8f))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                )
            }

            Text(
                text = if (distanceMeters != null) "$label · ${distanceMeters.roundToInt()} м" else label,
                style = ArType.LabelArchiveCode,
                color = ArColors.OnTertiaryContainer,
                modifier = Modifier
                    .clip(RoundedCornerShape(8.dp))
                    .background(ArColors.TertiaryContainer.copy(alpha = 0.9f))
                    .padding(horizontal = 8.dp, vertical = 3.dp),
            )
        }
    }
}

/** Расходящиеся круги вокруг метки — «здесь». */
@Composable
private fun RadarPulse(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "radar")
    val wave by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1600), RepeatMode.Restart),
        label = "wave",
    )

    Box(modifier = modifier.size(48.dp), contentAlignment = Alignment.Center) {
        Box(
            Modifier
                .size(48.dp)
                .scale(0.5f + wave * 0.5f)
                .alpha((1f - wave) * 0.35f)
                .clip(CircleShape)
                .background(ArColors.TertiaryFixed),
        )
        Box(
            Modifier
                .size(24.dp)
                .clip(CircleShape)
                .background(ArColors.Tertiary),
            contentAlignment = Alignment.Center,
        ) {
            Text("◎", style = ArType.LabelAction, color = ArColors.OnTertiary)
        }
    }
}

/**
 * Подсказка «поверни туда», когда цель за пределами кадра.
 * Без неё пользователь крутится на месте и не понимает, куда смотреть.
 */
@Composable
internal fun OffScreenArrow(
    hint: OffScreenHint,
    distanceMeters: Double?,
    modifier: Modifier = Modifier,
) {
    if (hint == OffScreenHint.NONE) return

    Row(
        modifier = modifier
            .clip(RoundedCornerShape(999.dp))
            .background(ArColors.InverseSurface.copy(alpha = 0.8f))
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        if (hint == OffScreenHint.LEFT) {
            Text("‹", style = ArType.HeadlineSm, color = ArColors.TertiaryFixed)
        }
        Text(
            text = buildString {
                append("Поверните ")
                append(if (hint == OffScreenHint.LEFT) "левее" else "правее")
                if (distanceMeters != null) append(" · ${distanceMeters.roundToInt()} м")
            },
            style = ArType.LabelArchiveCode,
            color = ArColors.SurfaceBright,
        )
        if (hint == OffScreenHint.RIGHT) {
            Text("›", style = ArType.HeadlineSm, color = ArColors.TertiaryFixed)
        }
    }
}
