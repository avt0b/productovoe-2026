package ru.marshruty.ar.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import ru.marshruty.ar.NarrationPlayback
import ru.marshruty.ar.domain.buildSceneState
import ru.marshruty.ar.sim.Simulation

/**
 * Превью экрана в разных состояниях.
 *
 * Это не витрина, а рабочий инструмент: каждое состояние — то, которое тяжело
 * или невозможно поймать руками на устройстве. Открывается в панели Preview
 * Android Studio без телефона и без камеры.
 */

/** Имитация кадра: рассветное поле вместо камеры. */
@Composable
private fun BoxScope.FakeCameraFeed() {
    Box(
        Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    listOf(
                        Color(0xFF9DB2C4),
                        Color(0xFFC8C3A4),
                        Color(0xFF6E7355),
                        Color(0xFF3D4331),
                    ),
                ),
            ),
    )
}

@Preview(name = "Цель в кадре", widthDp = 400, heightDp = 880)
@Composable
private fun PreviewTargetInFrame() {
    ArScreen(
        spec = Simulation.point,
        scene = buildSceneState(
            fix = Simulation.fix,
            orientation = Simulation.facingTarget(),
            target = Simulation.Target,
        ),
        playback = NarrationPlayback(positionMillis = 2_000, isPlaying = true),
        actions = ArScreenActions(),
        cameraFeed = { FakeCameraFeed() },
    )
}

@Preview(name = "Цель за кадром слева", widthDp = 400, heightDp = 880)
@Composable
private fun PreviewTargetOffScreen() {
    ArScreen(
        spec = Simulation.point,
        scene = buildSceneState(
            fix = Simulation.fix,
            orientation = Simulation.turnedAwayBy(-80.0),
            target = Simulation.Target,
        ),
        playback = NarrationPlayback(positionMillis = 8_000, isPlaying = true),
        actions = ArScreenActions(),
        cameraFeed = { FakeCameraFeed() },
    )
}

@Preview(name = "Плохой GPS", widthDp = 400, heightDp = 880)
@Composable
private fun PreviewUnreliableLocation() {
    ArScreen(
        spec = Simulation.point,
        scene = buildSceneState(
            fix = Simulation.poorFix,
            orientation = Simulation.facingTarget(),
            target = Simulation.Target,
        ),
        playback = NarrationPlayback(positionMillis = 1_000, isPlaying = false, isMuted = true),
        actions = ArScreenActions(),
        cameraFeed = { FakeCameraFeed() },
    )
}

@Preview(name = "Находка подтверждена", widthDp = 400, heightDp = 880)
@Composable
private fun PreviewDiscovery() {
    ArScreen(
        spec = Simulation.point,
        scene = buildSceneState(
            fix = Simulation.fix,
            orientation = Simulation.facingTarget(),
            target = Simulation.Target,
        ),
        playback = NarrationPlayback(positionMillis = 14_000, isPlaying = true),
        actions = ArScreenActions(),
        discoveryMessage = "Координата связистов подтверждена",
        cameraFeed = { FakeCameraFeed() },
    )
}

@Preview(name = "Мемориал — без проводника", widthDp = 400, heightDp = 880)
@Composable
private fun PreviewMemorialWithoutCompanion() {
    // Проверка этического правила: у братской могилы проводника быть не должно,
    // и экран обязан выглядеть законченным без него.
    ArScreen(
        spec = Simulation.memorialPoint,
        scene = buildSceneState(
            fix = Simulation.fix,
            orientation = Simulation.facingTarget(),
            target = null,
        ),
        playback = NarrationPlayback(positionMillis = 3_000, isPlaying = true),
        actions = ArScreenActions(),
        cameraFeed = { FakeCameraFeed() },
    )
}

@Preview(name = "Камера недоступна", widthDp = 400, heightDp = 880)
@Composable
private fun PreviewCameraUnavailable() {
    ArScreen(
        spec = Simulation.point,
        scene = buildSceneState(
            fix = Simulation.fix,
            orientation = Simulation.facingTarget(),
            target = Simulation.Target,
        ),
        playback = NarrationPlayback(),
        actions = ArScreenActions(),
    )
}
