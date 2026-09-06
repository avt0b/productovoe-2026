package ru.marshruty.ar.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import ru.marshruty.ar.ArPointSpec
import ru.marshruty.ar.NarrationPlayback
import ru.marshruty.ar.domain.ArSceneState
import ru.marshruty.ar.domain.OffScreenHint
import ru.marshruty.ar.lineAt

/** Обратные вызовы экрана наружу. */
data class ArScreenActions(
    val onClose: () -> Unit = {},
    val onToggleMute: () -> Unit = {},
    val onReplay: () -> Unit = {},
    val onAim: () -> Unit = {},
    val onMarkerTap: () -> Unit = {},
    val onCompanionTap: () -> Unit = {},
)

/**
 * AR-экран целиком.
 *
 * Кадр камеры приходит слотом [cameraFeed]: в бою туда кладут `PreviewView`
 * от CameraX, в Preview и в режиме симуляции — статичную картинку. Благодаря
 * этому весь экран рисуется в студии без телефона и показывается на защите
 * без окна и неба.
 *
 * Состояние [scene] целиком посчитано в домене и покрыто тестами — здесь
 * только отрисовка, без вычислений.
 */
@Composable
fun ArScreen(
    spec: ArPointSpec,
    scene: ArSceneState,
    playback: NarrationPlayback,
    actions: ArScreenActions,
    modifier: Modifier = Modifier,
    discoveryMessage: String? = null,
    cameraFeed: @Composable BoxScope.() -> Unit = { CameraUnavailablePlaceholder() },
) {
    Box(modifier = modifier.fillMaxSize().background(Color.Black)) {
        cameraFeed()

        EdgeScrim()
        ViewfinderReticle()

        scene.markerPosition?.let { position ->
            TargetMarker(
                position = position,
                label = spec.target?.label.orEmpty(),
                distanceMeters = scene.distanceMeters,
                coordinatesText = spec.target?.let { formatCoordinates(it.point.latitude, it.point.longitude) },
                onClick = actions.onMarkerTap,
            )
        }

        // --- верхний слой управления ---
        Column(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .systemBarsPadding()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            StoryProgressBar(progress = spec.progress)

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                HudIconButton("✕", "Закрыть AR-режим", actions.onClose)
                StepChip(spec.stepIndex, spec.stepTotal, spec.title)
                HudIconButton(
                    glyph = if (playback.isMuted) "🔇" else "🔊",
                    contentDescription = if (playback.isMuted) "Включить звук" else "Выключить звук",
                    onClick = actions.onToggleMute,
                )
            }

            CompassStrip(scene.orientation)

            if (scene.locationUnreliable) {
                UnreliableLocationNotice()
            } else if (scene.offScreenHint != OffScreenHint.NONE) {
                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    OffScreenArrow(scene.offScreenHint, scene.distanceMeters)
                }
            }
        }

        AnimatedVisibility(
            visible = discoveryMessage != null,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier
                .align(Alignment.TopCenter)
                .systemBarsPadding()
                .padding(top = 140.dp),
        ) {
            DiscoveryToast(discoveryMessage.orEmpty())
        }

        // --- нижний слой: проводник и его реплика ---
        Column(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .systemBarsPadding()
                .padding(horizontal = 16.dp, vertical = 16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            spec.companion?.let { companion ->
                CompanionCharacter(
                    spec = companion,
                    onTap = actions.onCompanionTap,
                    modifier = Modifier.padding(bottom = 4.dp),
                )
                DialoguePanel(
                    spec = companion,
                    subtitle = spec.narration.subtitles.lineAt(playback.positionMillis)?.text,
                    isSpeaking = playback.isPlaying && !playback.isMuted,
                    aimLabel = spec.target?.let { "Навести на цель" },
                    onReplay = actions.onReplay,
                    onAim = actions.onAim,
                )
            }
        }
    }
}

/** Кадр не получен: чёрный экран без объяснения выглядит как поломка. */
@Composable
internal fun CameraUnavailablePlaceholder(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier.fillMaxSize().background(ArColors.InverseSurface),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            "КАДР КАМЕРЫ НЕДОСТУПЕН",
            style = ArType.LabelArchiveCode,
            color = ArColors.SurfaceBright.copy(alpha = 0.6f),
        )
    }
}

/** Координаты в привычном для карт виде: 52°58'14"N 36°04'02"E. */
internal fun formatCoordinates(latitude: Double, longitude: Double): String {
    fun part(value: Double, positive: String, negative: String): String {
        val hemisphere = if (value >= 0) positive else negative
        val absolute = kotlin.math.abs(value)
        val degrees = absolute.toInt()
        val minutesFull = (absolute - degrees) * 60.0
        val minutes = minutesFull.toInt()
        val seconds = ((minutesFull - minutes) * 60.0).toInt()
        return "%d°%02d'%02d\"%s".format(degrees, minutes, seconds, hemisphere)
    }
    return "${part(latitude, "N", "S")} ${part(longitude, "E", "W")}"
}
