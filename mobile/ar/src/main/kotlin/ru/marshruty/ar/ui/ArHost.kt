package ru.marshruty.ar.ui

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ru.marshruty.ar.ArPointSpec
import ru.marshruty.ar.ArResult
import ru.marshruty.ar.NarrationPlayback
import ru.marshruty.ar.data.CameraOpticsSource
import ru.marshruty.ar.data.PlatformLocationSource
import ru.marshruty.ar.data.SensorOrientationSource
import ru.marshruty.ar.domain.CameraFieldOfView
import ru.marshruty.ar.domain.DeviceOrientation
import ru.marshruty.ar.domain.croppedFieldOfView
import ru.marshruty.ar.domain.buildSceneState

/** Соотношение сторон кадра, который отдаёт CameraX по умолчанию. */
private const val FRAME_ASPECT_RATIO = 3.0 / 4.0

/**
 * Сборка экрана из живых источников.
 *
 * Здесь и только здесь модуль трогает Android: камеру, датчики, геолокацию
 * и разрешения. Всё остальное — чистые функции и composable, которые об этом
 * не знают и потому проверяются без устройства.
 */
@Composable
fun ArHost(
    spec: ArPointSpec,
    onFinish: (ArResult) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val configuration = LocalConfiguration.current

    val locationSource = remember { PlatformLocationSource(context) }
    val orientationSource = remember {
        SensorOrientationSource(context, locationProvider = { locationSource.lastPoint })
    }
    val opticsSource = remember { CameraOpticsSource(context) }

    var cameraGranted by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED,
        )
    }
    var permissionAsked by remember { mutableStateOf(false) }
    var cameraFailed by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { granted ->
        permissionAsked = true
        cameraGranted = granted[Manifest.permission.CAMERA] == true
    }

    LaunchedEffect(Unit) {
        if (!cameraGranted || !locationSource.hasPermission) {
            permissionLauncher.launch(
                arrayOf(Manifest.permission.CAMERA, Manifest.permission.ACCESS_FINE_LOCATION),
            )
        }
    }

    // Датчика вращения может не быть — тогда AR бессмысленен, и хост
    // должен показать обычную карточку точки, а не пустой экран.
    LaunchedEffect(orientationSource.isAvailable) {
        if (!orientationSource.isAvailable) {
            onFinish(ArResult.Unavailable(spec.pointId, ArResult.Unavailable.Reason.NO_ORIENTATION_SENSOR))
        }
    }
    LaunchedEffect(permissionAsked, cameraGranted) {
        if (permissionAsked && !cameraGranted) {
            onFinish(ArResult.Unavailable(spec.pointId, ArResult.Unavailable.Reason.CAMERA_PERMISSION_DENIED))
        }
    }

    var fieldOfView by remember { mutableStateOf(CameraFieldOfView.Default) }
    LaunchedEffect(configuration.screenWidthDp, configuration.screenHeightDp) {
        val full = opticsSource.fieldOfView()
        val viewAspect = configuration.screenWidthDp.toDouble() /
            configuration.screenHeightDp.toDouble().coerceAtLeast(1.0)
        fieldOfView = croppedFieldOfView(full, viewAspect, FRAME_ASPECT_RATIO)
    }

    val orientation by orientationSource.orientation
        .collectAsStateWithLifecycle(initialValue = DeviceOrientation(0.0, 0.0))
    val needsCalibration by orientationSource.needsCalibration
        .collectAsStateWithLifecycle(initialValue = false)
    val fix by locationSource.fix.collectAsStateWithLifecycle(initialValue = null)

    var discovery by remember { mutableStateOf<String?>(null) }
    var playback by remember { mutableStateOf(NarrationPlayback(isPlaying = true)) }

    val scene = buildSceneState(
        fix = fix,
        orientation = orientation,
        target = spec.target?.point,
        targetHeightOffsetMeters = spec.target?.heightOffsetMeters ?: 0.0,
        fieldOfView = fieldOfView,
    )

    Box(modifier = modifier.fillMaxSize()) {
        ArScreen(
            spec = spec,
            scene = scene,
            playback = playback,
            discoveryMessage = discovery,
            actions = ArScreenActions(
                onClose = { onFinish(ArResult.Dismissed(spec.pointId)) },
                onToggleMute = { playback = playback.copy(isMuted = !playback.isMuted) },
                onReplay = { playback = playback.copy(positionMillis = 0, isPlaying = true) },
                onAim = { discovery = spec.target?.label?.let { "Наведитесь на «$it»" } },
                onMarkerTap = {
                    discovery = "Координата подтверждена"
                    onFinish(ArResult.Completed(spec.pointId))
                },
                onCompanionTap = { playback = playback.copy(isPlaying = !playback.isPlaying) },
            ),
            cameraFeed = {
                if (cameraGranted && !cameraFailed) {
                    CameraPreview(
                        modifier = Modifier.fillMaxSize(),
                        onFailure = { cameraFailed = true },
                    )
                } else {
                    CameraUnavailablePlaceholder()
                }
            },
        )

        if (needsCalibration) {
            CalibrationHint(
                modifier = Modifier
                    .align(Alignment.Center)
                    .padding(24.dp)
                    .clickable { },
            )
        }
    }
}

/**
 * Подсказка о калибровке компаса.
 *
 * Без неё пользователь видит, что метка стоит не там, и решает, что приложение
 * сломано, — хотя дело в магнитометре, который сбивается рядом с металлом.
 */
@Composable
private fun CalibrationHint(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(ArColors.InverseSurface.copy(alpha = 0.9f))
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text("КОМПАС СБИТ", style = ArType.LabelArchiveCode, color = ArColors.TertiaryFixedDim)
        Text(
            "Поводите телефоном «восьмёркой» несколько секунд.\nРядом с металлом компас врёт.",
            style = ArType.BodySm,
            color = ArColors.InverseOnSurface,
            textAlign = TextAlign.Center,
        )
    }
}
