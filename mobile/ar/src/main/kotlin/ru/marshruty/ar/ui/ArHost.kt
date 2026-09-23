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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.runtime.withFrameMillis
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.coroutines.delay
import ru.marshruty.ar.ArPointSpec
import ru.marshruty.ar.ArResult
import ru.marshruty.ar.NarrationPlayback
import ru.marshruty.ar.data.CameraOpticsSource
import ru.marshruty.ar.data.PlatformLocationSource
import ru.marshruty.ar.data.SensorOrientationSource
import ru.marshruty.ar.domain.CameraFieldOfView
import ru.marshruty.ar.domain.CompanionAction
import ru.marshruty.ar.domain.DeviceOrientation
import ru.marshruty.ar.domain.MarkerStatus
import ru.marshruty.ar.domain.buildSceneState
import ru.marshruty.ar.domain.croppedFieldOfView
import ru.marshruty.ar.domain.fittedTo
import ru.marshruty.ar.domain.flipTransform
import ru.marshruty.ar.domain.narrationPositionMillis
import ru.marshruty.ar.domain.resolveCompanionAction
import ru.marshruty.ar.durationMillis
import ru.marshruty.ar.stablePositionAt

/** Соотношение сторон кадра, который отдаёт CameraX по умолчанию. */
private const val FRAME_ASPECT_RATIO = 3.0 / 4.0

/**
 * Как часто спрашивать, где идёт рассказ, мс.
 *
 * Строка субтитров живёт секунды, так что чаще незачем; реже — и смена строки
 * начнёт запаздывать за голосом заметно на слух.
 */
private const val NARRATION_POLL_MILLIS = 100L

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

    // Угол обзора кадра ARCore приходит из сцены маркера. До первого кадра
    // и в компасном режиме работает расчёт под CameraX.
    var markerFieldOfView by remember { mutableStateOf<CameraFieldOfView?>(null) }

    val orientation by orientationSource.orientation
        .collectAsStateWithLifecycle(initialValue = DeviceOrientation(0.0, 0.0))
    val needsCalibration by orientationSource.needsCalibration
        .collectAsStateWithLifecycle(initialValue = false)
    val fix by locationSource.fix.collectAsStateWithLifecycle(initialValue = null)

    var discovery by remember { mutableStateOf<String?>(null) }

    // Одни часы на всё: по ним и субтитры сменяются, и кадры персонажа идут.
    // Держать два независимых таймера — верный способ рассинхронить речь и рот.
    //
    // Тело хоста часы не читает. Иначе экран целиком перерисовывался бы каждый
    // кадр — на этом телефоне 120 раз в секунду — ради субтитров, которые
    // меняются раз в несколько секунд. Часы читают только derivedStateOf ниже:
    // перерисовка случается, когда меняется результат, а не время.
    val clock = remember { mutableLongStateOf(0L) }
    LaunchedEffect(Unit) {
        var startedAt = 0L
        while (true) {
            withFrameMillis { frameTimeMillis ->
                if (startedAt == 0L) startedAt = frameTimeMillis
                clock.longValue = frameTimeMillis - startedAt
            }
        }
    }

    // Голос проводника. null — озвучки на точку нет, рассказ идёт субтитрами.
    val narration = rememberNarrationSound(spec.narration.audioUri)

    // Длина записи известна не сразу — плеер сообщает её, когда подготовится.
    val audioDuration = remember { mutableLongStateOf(0L) }

    // Субтитры, нарезанные хостом на глаз, подгоняются под голос. Настоящие
    // таймкоды остаются как есть: они точнее любой оценки.
    val shownSpec = remember(spec, audioDuration.longValue) {
        val duration = audioDuration.longValue
        if (!spec.narration.subtitlesAreEstimated || duration <= 0) {
            spec
        } else {
            spec.copy(narration = spec.narration.copy(subtitles = spec.narration.subtitles.fittedTo(duration)))
        }
    }
    val narrationDuration = remember(shownSpec.narration) { shownSpec.narration.subtitles.durationMillis() }

    var narrationStartedAt by remember { mutableLongStateOf(0L) }
    var pausedPosition by remember { mutableLongStateOf(0L) }
    var isMuted by remember { mutableStateOf(false) }
    var isPlaying by remember { mutableStateOf(true) }
    var trickStartedAt by remember { mutableStateOf<Long?>(null) }

    // Рассказ начинается сам: человек пришёл на точку слушать, а не нажимать.
    LaunchedEffect(narration) { narration?.play() }

    // Маркер задан и ARCore работает — проводник стоит на табличке в 3D.
    // Иначе прежний режим: кадр CameraX, компас и плоский персонаж внизу.
    var markerUnavailable by remember { mutableStateOf(false) }
    val activeMarker = spec.marker?.takeIf { !markerUnavailable }
    var markerStatus by remember { mutableStateOf<MarkerStatus?>(null) }

    // 3D-модель рисуется только внутри сцены ARCore; без неё — покадровая ветка.
    val companionAsset = spec.companion?.assetUri.orEmpty()
    val isModel = companionAsset.endsWith(".glb", ignoreCase = true)

    val frames = rememberCompanionFrames(if (isModel) "" else companionAsset)
    val trickClip = frames.trickClip()
    val isSpeaking = isPlaying && !isMuted

    // Позиция рассказа. Плеер опрашивается не каждый кадр: сто двадцать
    // обращений в секунду ради строки, которая держится шесть секунд, — пустая
    // работа. Со звуком позицию задаёт он, без звука — часы экрана.
    val narrationPosition = remember { mutableLongStateOf(0L) }
    LaunchedEffect(narration, spec.narration) {
        while (true) {
            narration?.durationMillis?.let { known ->
                if (audioDuration.longValue != known) audioDuration.longValue = known
            }
            // Без звука пауза должна останавливать и субтитры: часы-то идут.
            if (isPlaying || narration != null) {
                narrationPosition.longValue = narrationPositionMillis(
                    audioPositionMillis = narration?.positionMillis,
                    clockMillis = clock.longValue,
                    startedAtMillis = narrationStartedAt,
                )
            }
            // Рассказ дослушан — проводник замолкает. Иначе он «говорит» в
            // тишину до самого выхода с точки.
            val finished = narration?.isFinished
                ?: (narrationDuration > 0 && narrationPosition.longValue >= narrationDuration)
            if (isPlaying && finished) isPlaying = false
            delay(NARRATION_POLL_MILLIS)
        }
    }

    val subtitlePosition by remember(shownSpec.narration) {
        derivedStateOf { shownSpec.narration.subtitles.stablePositionAt(narrationPosition.longValue) }
    }
    val actionState = remember(trickClip, isSpeaking) {
        derivedStateOf {
            resolveCompanionAction(
                trickElapsedMillis = trickStartedAt?.let { clock.longValue - it },
                trickClip = trickClip,
                isSpeaking = isSpeaking,
            )
        }
    }
    // Сальто трансформацией — только когда своих кадров трюка нет, иначе
    // персонаж крутанётся дважды: и нарисованно, и программно.
    val flipState = remember(frames, trickClip) {
        derivedStateOf {
            val started = trickStartedAt
            if (started == null || frames.has(CompanionAction.TRICK)) {
                null
            } else {
                val elapsed = clock.longValue - started
                if (trickClip.isFinished(elapsed)) null else flipTransform(elapsed.toFloat() / trickClip.durationMillis)
            }
        }
    }
    val frameIndexState = remember(frames, actionState) {
        derivedStateOf {
            val action = actionState.value
            val elapsed = if (action == CompanionAction.TRICK) {
                trickStartedAt?.let { clock.longValue - it } ?: 0L
            } else {
                clock.longValue
            }
            frames.clipFor(action)?.frameAt(elapsed) ?: 0
        }
    }

    // Трюк доигран — отпускаем состояние, иначе персонаж застрянет на последнем кадре.
    LaunchedEffect(actionState) {
        snapshotFlow { actionState.value }.collect { action ->
            if (action != CompanionAction.TRICK) trickStartedAt = null
        }
    }

    val scene = buildSceneState(
        fix = fix,
        orientation = orientation,
        target = spec.target?.point,
        targetHeightOffsetMeters = spec.target?.heightOffsetMeters ?: 0.0,
        fieldOfView = markerFieldOfView?.takeIf { activeMarker != null } ?: fieldOfView,
    )

    Box(modifier = modifier.fillMaxSize()) {
        ArScreen(
            spec = shownSpec,
            scene = scene,
            playback = NarrationPlayback(
                positionMillis = subtitlePosition,
                isPlaying = isPlaying,
                isMuted = isMuted,
            ),
            discoveryMessage = discovery,
            actions = ArScreenActions(
                onClose = { onFinish(ArResult.Dismissed(spec.pointId)) },
                onToggleMute = {
                    isMuted = !isMuted
                    // Звук глушим, рассказ идёт: субтитры продолжают, и человек
                    // не теряет место, где остановился.
                    narration?.setMuted(isMuted)
                },
                onTogglePlay = {
                    if (isPlaying) {
                        pausedPosition = narrationPosition.longValue
                        narration?.pause()
                    } else {
                        // Часы экрана идут всегда, поэтому «продолжить» — это
                        // сдвинуть начало рассказа, а не запустить их заново.
                        narrationStartedAt = clock.longValue - pausedPosition
                        narration?.play()
                    }
                    isPlaying = !isPlaying
                },
                onReplay = {
                    narrationStartedAt = clock.longValue
                    pausedPosition = 0L
                    narration?.replay()
                    isPlaying = true
                },
                onAim = { discovery = spec.target?.label?.let { "Наведитесь на «$it»" } },
                onMarkerTap = {
                    discovery = "Координата подтверждена"
                    onFinish(ArResult.Completed(spec.pointId))
                },
                onCompanionTap = { trickStartedAt = clock.longValue },
                onTrick = { trickStartedAt = clock.longValue },
            ),
            cameraFeed = {
                // Камеру держит кто-то один: либо ARCore, либо CameraX. Вдвоём
                // они её не откроют.
                when {
                    !cameraGranted -> CameraUnavailablePlaceholder()
                    activeMarker != null -> ArMarkerScene(
                        marker = activeMarker,
                        companionAsset = companionAsset.takeIf { isModel && spec.companion != null },
                        flip = { flipState.value },
                        onStatusChange = { markerStatus = it },
                        onFieldOfView = { full, frameAspect ->
                            val viewAspect = configuration.screenWidthDp.toDouble() /
                                configuration.screenHeightDp.toDouble().coerceAtLeast(1.0)
                            markerFieldOfView = croppedFieldOfView(full, viewAspect, frameAspect)
                        },
                        onUnavailable = {
                            markerUnavailable = true
                            markerStatus = null
                        },
                    )
                    !cameraFailed -> CameraPreview(
                        modifier = Modifier.fillMaxSize(),
                        onFailure = { cameraFailed = true },
                    )
                    else -> CameraUnavailablePlaceholder()
                }
            },
            // С маркером 3D-проводник стоит в сцене — плоская фигура внизу была бы вторым персонажем.
            companionArtwork = if (activeMarker != null && isModel) {
                null
            } else {
                {
                    // Состояния читаются здесь, внутри слота: при смене кадра спрайта
                    // перерисовывается только фигура, а не весь экран.
                    SpriteArtwork(
                        frames = frames,
                        action = actionState.value,
                        frameIndex = frameIndexState.value,
                        modifier = Modifier.size(width = 190.dp, height = 190.dp),
                        flip = flipState.value,
                    )
                }
            },
            markerStatus = markerStatus.takeIf { activeMarker != null },
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
