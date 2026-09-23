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
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import ru.marshruty.ar.CompanionSpec

/**
 * Проводник в нижней трети кадра.
 *
 * Ассет передаётся слотом [artwork]: модуль не тащит картинку в себя, поэтому
 * экран открывается в Preview и в режиме симуляции без файлов персонажа.
 * По макету это плоское изображение с мягкой тенью-подложкой под лапами —
 * ни ARCore, ни постановки на плоскость не требуется.
 */
@Composable
internal fun CompanionCharacter(
    spec: CompanionSpec,
    onTap: () -> Unit,
    modifier: Modifier = Modifier,
    artwork: @Composable () -> Unit = { CompanionPlaceholder() },
) {
    Box(
        modifier = modifier.size(width = 224.dp, height = 200.dp),
        contentAlignment = Alignment.BottomCenter,
    ) {
        // Тень-подложка: без неё персонаж «висит» и на ярком фоне теряется.
        Box(
            Modifier
                .align(Alignment.BottomCenter)
                .width(160.dp)
                .height(22.dp)
                .clip(CircleShape)
                .background(ArColors.InverseSurface.copy(alpha = 0.35f)),
        )

        Box(Modifier.clickable(onClick = onTap), contentAlignment = Alignment.BottomCenter) {
            artwork()
        }

        Row(
            modifier = Modifier
                .align(Alignment.TopEnd)
                .clip(RoundedCornerShape(999.dp))
                .background(ArColors.SurfaceBright.copy(alpha = 0.95f))
                .padding(horizontal = 10.dp, vertical = 5.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text("🐾", style = ArType.BodySm)
            Text(spec.name.substringAfterLast(' '), style = ArType.LabelAction, color = ArColors.Tertiary)
        }
    }
}

/** Заглушка персонажа, пока нет ассета: силуэт вместо пустоты. */
@Composable
internal fun CompanionPlaceholder(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .size(width = 170.dp, height = 170.dp)
            .clip(RoundedCornerShape(20.dp))
            .background(ArColors.InverseSurface.copy(alpha = 0.55f)),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("🐕‍🦺", style = ArType.MemorialQuote.copy(fontSize = androidx.compose.ui.unit.TextUnit.Unspecified))
        Text(
            "ассет проводника\nне подключён",
            style = ArType.LabelArchiveCode,
            color = ArColors.SurfaceBright.copy(alpha = 0.7f),
            textAlign = TextAlign.Center,
        )
    }
}

/** Панель с репликой проводника и действиями. */
@Composable
internal fun DialoguePanel(
    spec: CompanionSpec,
    subtitle: String?,
    isSpeaking: Boolean,
    aimLabel: String?,
    onReplay: () -> Unit,
    onAim: () -> Unit,
    modifier: Modifier = Modifier,
    /** Рассказ идёт: кнопка предлагает паузу, а не продолжение. */
    isPlaying: Boolean = true,
    onTogglePlay: () -> Unit = {},
    /** Трюк по кнопке. null — у персонажа нет такого клипа. */
    onTrick: (() -> Unit)? = null,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(ArColors.InverseSurface.copy(alpha = 0.92f))
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Box(
                    Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(ArColors.TertiaryFixedDim),
                )
                Text(spec.name, style = ArType.HeadlineSm, color = ArColors.TertiaryFixed)
                Text(
                    spec.subtitle,
                    style = ArType.LabelArchiveCode,
                    color = ArColors.SurfaceContainerHighest,
                )
            }
            if (isSpeaking) SoundWave()
        }

        Text(
            text = subtitle ?: "…",
            style = ArType.MemorialQuote,
            color = ArColors.SurfaceBright,
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Только глиф: четыре подписи в ряд не помещаются на узком экране.
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(8.dp))
                    .background(ArColors.SurfaceContainerHighest.copy(alpha = 0.2f))
                    .clickable(onClick = onTogglePlay)
                    .padding(horizontal = 14.dp, vertical = 10.dp)
                    .semantics {
                        contentDescription = if (isPlaying) "Поставить рассказ на паузу" else "Продолжить рассказ"
                    },
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = if (isPlaying) "⏸" else "▶",
                    style = ArType.LabelAction,
                    color = ArColors.TertiaryFixed,
                )
            }

            Row(
                modifier = Modifier
                    .clip(RoundedCornerShape(8.dp))
                    .background(ArColors.SurfaceContainerHighest.copy(alpha = 0.2f))
                    .clickable(onClick = onReplay)
                    .padding(horizontal = 12.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text("↻", style = ArType.LabelAction, color = ArColors.TertiaryFixed)
                Text("Повторить", style = ArType.LabelAction, color = ArColors.SurfaceBright)
            }

            if (onTrick != null) {
                Row(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(ArColors.SurfaceContainerHighest.copy(alpha = 0.2f))
                        .clickable(onClick = onTrick)
                        .padding(horizontal = 12.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text("↻", style = ArType.LabelAction, color = ArColors.TertiaryFixedDim)
                    Text("Сальто", style = ArType.LabelAction, color = ArColors.SurfaceBright)
                }
            }

            if (aimLabel != null) {
                Row(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(8.dp))
                        .background(ArColors.TertiaryContainer)
                        .clickable(onClick = onAim)
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center,
                ) {
                    Text(aimLabel, style = ArType.LabelAction, color = ArColors.OnTertiary)
                }
            }
        }
    }
}

/** Индикатор звучащей речи — четыре полоски, как в макете. */
@Composable
private fun SoundWave(modifier: Modifier = Modifier) {
    val transition = rememberInfiniteTransition(label = "wave")
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(3.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        listOf(12, 18, 8, 22).forEachIndexed { index, peak ->
            val factor by transition.animateFloat(
                initialValue = 0.35f,
                targetValue = 1f,
                animationSpec = infiniteRepeatable(
                    tween(durationMillis = 520 + index * 90),
                    RepeatMode.Reverse,
                ),
                label = "bar$index",
            )
            Box(
                Modifier
                    .width(2.dp)
                    .height((peak * factor).dp)
                    .clip(CircleShape)
                    .background(ArColors.TertiaryFixed)
                    .alpha(0.9f),
            )
        }
    }
}
