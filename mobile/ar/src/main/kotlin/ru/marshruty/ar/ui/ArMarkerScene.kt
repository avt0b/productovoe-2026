package ru.marshruty.ar.ui

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Log
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import com.google.ar.core.AugmentedImage
import com.google.ar.core.AugmentedImageDatabase
import com.google.ar.core.Config
import com.google.ar.core.Session
import com.google.ar.core.TrackingState
import io.github.sceneview.ar.ARCoreAvailability
import io.github.sceneview.ar.ARSceneView
import io.github.sceneview.ar.arcore.configure
import io.github.sceneview.math.Position
import io.github.sceneview.math.Rotation
import io.github.sceneview.math.Scale
import io.github.sceneview.model.ModelInstance
import io.github.sceneview.rememberEngine
import io.github.sceneview.rememberModelLoader
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import ru.marshruty.ar.MarkerSpec
import ru.marshruty.ar.data.QrScanner
import ru.marshruty.ar.domain.CameraFieldOfView
import ru.marshruty.ar.domain.CompanionPlacement
import ru.marshruty.ar.domain.DEFAULT_COMPANION_HEIGHT_METERS
import ru.marshruty.ar.domain.FlipTransform
import ru.marshruty.ar.domain.MarkerPose
import ru.marshruty.ar.domain.MarkerStatus
import ru.marshruty.ar.domain.PlacementSmoother
import ru.marshruty.ar.domain.Vec3
import ru.marshruty.ar.domain.companionHeightFor
import ru.marshruty.ar.domain.fieldOfViewFromIntrinsics
import ru.marshruty.ar.domain.placeCompanion
import ru.marshruty.ar.domain.poseInFrontOfCamera
import ru.marshruty.ar.domain.qrTriggersCompanion
import kotlin.math.sin
import io.github.sceneview.node.Node as NodeImpl

/**
 * Сцена ARCore: кадр камеры, трекинг картинки-маркера и проводник на ней.
 *
 * Здесь и только здесь модуль пользуется ARCore. Компас и GPS отвечают на
 * вопрос «в какую сторону идти», а на вопрос «где именно стоит персонаж»
 * ответить не могут — у них ошибка в десятки метров и градусов. Табличка на
 * точке даёт позу с точностью до сантиметров, а мир вокруг ARCore держит сам:
 * если отвести камеру от таблички, проводник останется стоять где стоял.
 *
 * Модель ожидается нормализованной (tools/normalize_companion.py): рост 1.0,
 * ноги на нуле, лицом к +Z. Тогда рост в метрах — это просто масштаб.
 */
@Composable
internal fun ArMarkerScene(
    marker: MarkerSpec,
    companionAsset: String?,
    flip: () -> FlipTransform?,
    onStatusChange: (MarkerStatus) -> Unit,
    onFieldOfView: (full: CameraFieldOfView, frameAspectRatio: Double) -> Unit,
    onUnavailable: () -> Unit,
    modifier: Modifier = Modifier,
) {
    // Экран не должен ждать ARCore. Движок, материалы, сессия и камера поднимаются
    // на главном потоке около двух секунд (замер на Xiaomi 13 Lite: SceneView
    // ~0.6 с, сессия ARCore ~0.9 с, камера ~0.4 с), и всё это время на телефоне
    // висела замёрзшая кнопка предыдущего экрана — выглядело как зависание.
    // Теперь сначала показывается сам AR-экран с подписью, а сцена — кадром позже.
    var sceneAllowed by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) {
        // Два кадра: первый доходит до дисплея только к следующему vsync.
        withFrameNanos { }
        withFrameNanos { }
        sceneAllowed = true
    }
    if (sceneAllowed) {
        ArMarkerSceneContent(marker, companionAsset, flip, onStatusChange, onFieldOfView, onUnavailable, modifier)
    } else {
        ArStartingPlaceholder(modifier)
    }
}

/** Подпись на время подъёма ARCore: главный поток занят, так что без анимации. */
@Composable
private fun ArStartingPlaceholder(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier.fillMaxSize().background(ArColors.InverseSurface),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            "ЗАПУСКАЮ AR-КАМЕРУ",
            style = ArType.LabelArchiveCode,
            color = ArColors.SurfaceBright.copy(alpha = 0.7f),
        )
    }
}

@Composable
private fun ArMarkerSceneContent(
    marker: MarkerSpec,
    /** GLB проводника в `assets`, или null — на точке маркер без персонажа. */
    companionAsset: String?,
    /**
     * Текущая поза сальто. Функция, а не значение: её читает кадровый колбэк
     * сцены, и на время трюка не нужно перерисовывать композицию каждый кадр.
     */
    flip: () -> FlipTransform?,
    onStatusChange: (MarkerStatus) -> Unit,
    /**
     * Угол обзора кадра ARCore и соотношение сторон кадра в портрете. Кадр у ARCore
     * не тот, что у CameraX, — другое разрешение и другое кадрирование, и метка цели
     * по компасу с углом от CameraX съезжала бы к краям экрана.
     */
    onFieldOfView: (full: CameraFieldOfView, frameAspectRatio: Double) -> Unit,
    /** ARCore на устройстве нет или сессия не поднялась — хост вернётся к компасу. */
    onUnavailable: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val engine = rememberEngine()
    val modelLoader = rememberModelLoader(engine)
    // Асинхронная загрузка, а не rememberModelInstance: тот создаёт модель на
    // главном потоке и там же синхронно декодирует все текстуры — у Шрека это
    // семь PNG до 1024×1024. loadModel читает файл в фоне, а текстуры отдаёт
    // загрузчику gltfio: он декодирует их в своих потоках, пока сцена каждый
    // кадр докачивает загрузку.
    val model by produceState<ModelInstance?>(initialValue = null, modelLoader, companionAsset) {
        val path = companionAsset ?: return@produceState
        val loaded = modelLoader.loadModel(path)
        if (loaded == null) {
            Log.w(TAG, "Модель $path не загрузилась")
            return@produceState
        }
        // Отсечение по кадру для модели выключено. Filament отбрасывает меш, если
        // его коробка вне кадра, а коробки у модели со скелетом посчитаны без
        // скиннинга — в другой позе. У Шрека коробка головы висит выше настоящей
        // головы, и когда камера близко смотрит на табличку сверху, коробка уходит
        // из кадра: голова пропадала, хотя должна быть видна. Десять тысяч
        // треугольников дешевле нарисовать целиком, чем гадать с коробками.
        val renderables = engine.renderableManager
        loaded.renderableEntities.forEach { entity ->
            renderables.setCulling(renderables.getInstance(entity), false)
        }
        Log.d(TAG, "модель проводника загружена: $path")
        value = loaded.instance
        awaitDispose { modelLoader.destroyModel(loaded) }
    }
    val currentFlip = rememberUpdatedState(flip)
    val currentOnUnavailable = rememberUpdatedState(onUnavailable)
    val currentOnFieldOfView = rememberUpdatedState(onFieldOfView)

    var markerBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var session by remember { mutableStateOf<Session?>(null) }
    var status by remember { mutableStateOf(MarkerStatus.SEARCHING) }
    // Меняется один раз — когда проводнику впервые нашлось место. Сама поза
    // живёт в [CompanionRig] и в композицию не попадает.
    var placed by remember { mutableStateOf(false) }
    val memory = remember { TrackingMemory() }
    val rig = remember { CompanionRig() }
    val smoother = remember { PlacementSmoother() }
    val qrScanner = remember { QrScanner() }

    LaunchedEffect(status) {
        Log.d(TAG, "маркер: $status")
        onStatusChange(status)
    }

    LaunchedEffect(marker.assetPath) {
        val decoded = withContext(Dispatchers.IO) { decodeMarker(context.assets, marker.assetPath) }
        if (decoded == null) currentOnUnavailable.value() else markerBitmap = decoded
    }

    // Разбор картинки на особые точки — вне главного потока. ARCore переводит её
    // в оттенки серого попиксельно через Bitmap.getPixel; на картинке 1600×1100
    // это держало главный поток 2.5 секунды (замер MIUIScout на Xiaomi 13 Lite).
    LaunchedEffect(session, markerBitmap) {
        val live = session ?: return@LaunchedEffect
        val bitmap = markerBitmap ?: return@LaunchedEffect
        val built = withContext(Dispatchers.Default) {
            runCatching {
                AugmentedImageDatabase(live).apply {
                    val width = marker.physicalWidthMeters
                    if (width != null) addImage(MARKER_NAME, bitmap, width) else addImage(MARKER_NAME, bitmap)
                }
            }
        }
        built.onSuccess { database ->
            memory.database = live to database
            // Переконфигурация — уже на главном потоке: из фона Session.configure небезопасен.
            runCatching { live.configure { config -> config.augmentedImageDatabase = database } }
                .onFailure { Log.w(TAG, "Сессия не приняла базу маркеров", it) }
        }.onFailure { error ->
            Log.w(TAG, "ARCore не принял картинку как маркер", error)
            status = MarkerStatus.BAD_MARKER
        }
    }

    ARSceneView(
        modifier = modifier.fillMaxSize(),
        engine = engine,
        modelLoader = modelLoader,
        // Плоскости не нужны: персонаж стоит на картинке, а поиск пола — лишняя
        // нагрузка на процессор и сетка из точек поверх кадра.
        planeRenderer = false,
        planeFindingMode = Config.PlaneFindingMode.DISABLED,
        sessionConfiguration = { arSession, config ->
            config.focusMode = Config.FocusMode.AUTO
            // Глубина выключена намеренно. С ней ARCore прячет проводника за всем,
            // что ближе: за столом, за спиной соседа, за собственной рукой с
            // телефоном. Выглядит это не как реализм, а как «маскот пропал» —
            // именно так и терялся проводник, поставленный перед камерой в
            // комнате. Проводник должен быть виден всегда.
            config.depthMode = Config.DepthMode.DISABLED
            // Пауза и возврат в приложение переконфигурируют сессию — уже собранная
            // база не должна при этом теряться.
            memory.database?.takeIf { it.first === arSession }?.let { config.augmentedImageDatabase = it.second }
        },
        onSessionCreated = { created -> session = created },
        onSessionUpdated = { arSession, frame ->
            if (status != MarkerStatus.BAD_MARKER) {
                val image = arSession.getAllTrackables(AugmentedImage::class.java)
                    .firstOrNull { it.name == MARKER_NAME }
                // Позу берём только из полного трекинга: в LAST_KNOWN_POSE картинка
                // вне кадра, и ARCore отдаёт последнее известное, а не уточнённое.
                val fresh = image != null &&
                    image.trackingState == TrackingState.TRACKING &&
                    image.trackingMethod == AugmentedImage.TrackingMethod.FULL_TRACKING
                if (fresh) {
                    memory.markerPose = image.toMarkerPose()
                    memory.placedInFront = false
                    memory.measuredWidthMeters = image.extentX
                }
                rig.height = companionHeightFor(
                    explicitMeters = marker.companionHeightMeters,
                    knownWidthMeters = marker.physicalWidthMeters,
                    measuredWidthMeters = memory.measuredWidthMeters,
                    placedInFront = memory.placedInFront,
                )
                val measured = memory.measuredWidthMeters
                if (measured != null && kotlin.math.abs(measured - memory.loggedWidthMeters) > 0.01f) {
                    memory.loggedWidthMeters = measured
                    Log.d(TAG, "ширина маркера по ARCore: " + measured + " м, рост проводника: " + rig.height + " м")
                }

                val camera = frame.camera
                if (camera.trackingState != memory.cameraState) {
                    memory.cameraState = camera.trackingState
                    Log.d(TAG, "камера: ${camera.trackingState}, причина: ${camera.trackingFailureReason}")
                }
                // Размер текстуры известен только с первого кадра и за сессию не
                // меняется — сообщаем один раз, а не сорок раз в секунду.
                if (!memory.intrinsicsReported) {
                    val intrinsics = camera.textureIntrinsics
                    val size = intrinsics.imageDimensions
                    val focal = intrinsics.focalLength
                    if (size[0] > 0 && size[1] > 0 && focal[0] > 0f && focal[1] > 0f) {
                        memory.intrinsicsReported = true
                        currentOnFieldOfView.value(
                            fieldOfViewFromIntrinsics(focal[0], focal[1], size[0], size[1]),
                            minOf(size[0], size[1]).toDouble() / maxOf(size[0], size[1]),
                        )
                    }
                }

                val cameraTracking = camera.trackingState == TrackingState.TRACKING
                if (cameraTracking && memory.trackingSinceNanos == 0L) memory.trackingSinceNanos = frame.timestamp
                val eye = camera.pose.let { Vec3(it.tx().toDouble(), it.ty().toDouble(), it.tz().toDouble()) }

                // QR-код читается быстрее и надёжнее картинки: с экрана, с мятой
                // бумаги, под углом. Увидели свой код — проводник выходит сразу,
                // не дожидаясь ни таблички, ни таймера.
                if (marker.companionOnQr && memory.markerPose == null && cameraTracking &&
                    (frame.timestamp - memory.lastQrScanNanos) / 1_000_000L >= QR_SCAN_INTERVAL_MILLIS
                ) {
                    memory.lastQrScanNanos = frame.timestamp
                    val code = runCatching {
                        frame.acquireCameraImage().use { image -> qrScanner.read(image) }
                    }.getOrNull()
                    if (qrTriggersCompanion(marker.qrPayload, code)) {
                        Log.d(TAG, "QR принят, выводим проводника: $code")
                        memory.qrAccepted = true
                    }
                }

                // Таблички нет — ставим проводника перед человеком: по коду сразу,
                // иначе по истечении отведённого времени. Один раз, а не каждый
                // кадр: иначе он ездил бы вслед за камерой.
                val fallbackAfter = marker.fallbackInFrontAfterMillis
                val waitedLongEnough = fallbackAfter != null &&
                    (frame.timestamp - memory.trackingSinceNanos) / 1_000_000L >= fallbackAfter
                if (memory.markerPose == null && cameraTracking && (memory.qrAccepted || waitedLongEnough)) {
                    // Рост нужен до позы: в ней он задаёт, насколько центр фигуры
                    // ниже уровня глаз. Посчитанный по прежнему умолчанию, он
                    // подвешивал проводника на уровень груди — поза ставится один
                    // раз и потом не пересчитывается.
                    memory.placedInFront = true
                    rig.height = companionHeightFor(
                        explicitMeters = marker.companionHeightMeters,
                        knownWidthMeters = marker.physicalWidthMeters,
                        measuredWidthMeters = memory.measuredWidthMeters,
                        placedInFront = true,
                    )
                    // Камера ARCore смотрит вдоль своей -Z.
                    memory.markerPose = poseInFrontOfCamera(
                        eye = eye,
                        forward = camera.pose.zAxis.toVec3() * -1.0,
                        distanceMeters = IN_FRONT_DISTANCE_METERS,
                        companionHeightMeters = rig.height.toDouble(),
                    )
                    Log.d(
                        TAG,
                        "проводник перед камерой: рост ${rig.height} м, " +
                            "повод: ${if (memory.qrAccepted) "QR" else "истекло ожидание таблички"}",
                    )
                }

                val pose = memory.markerPose
                if (pose != null && cameraTracking) {
                    rig.placement = smoother.update(placeCompanion(pose, eye))
                    if (!placed) placed = true
                }

                status = when {
                    pose == null -> MarkerStatus.SEARCHING
                    !cameraTracking -> MarkerStatus.LOST
                    fresh -> MarkerStatus.TRACKING
                    memory.placedInFront -> MarkerStatus.IN_FRONT
                    else -> MarkerStatus.HOLDING
                }
            }
        },
        onARCoreAvailability = { availability ->
            // NotInstalled и NeedsUpdate не сдаём: встроенная плашка SceneView
            // сама предложит поставить или обновить сервисы AR.
            if (availability == ARCoreAvailability.Unsupported) currentOnUnavailable.value()
        },
        onSessionFailure = { failure ->
            Log.w(TAG, "Сессия ARCore не поднялась: $failure")
            currentOnUnavailable.value()
        },
    ) {
        // Делегированное свойство не приводится к не-null само — нужна локальная копия.
        val instance = model
        if (placed && instance != null) {
            // Дерево узлов строится один раз, а позу и рост пишет кадровый колбэк:
            // сглаживание, дыхание, сальто и уточнение размера таблички меняются
            // каждый кадр, дерево — никогда.
            //
            // Четыре узла вместо одной матрицы — у каждого своя точка опоры. Присед
            // сжимает от ног, иначе ступни отрываются от картинки; оборот идёт
            // вокруг пояса, иначе персонаж крутится вокруг пяток.
            Node(apply = { rig.anchor = this; onFrame = { nanos -> rig.update(nanos, currentFlip.value()) } }) {
                Node(apply = { rig.body = this }) {
                    Node(apply = { rig.spin = this }) {
                        Node(
                            apply = {
                                rig.sizer = this
                                // Последний узел создан — ставим всё дерево на место сразу,
                                // иначе первый кадр модель ростом в метр стоит в начале координат.
                                rig.update(frameTimeNanos = 0L, flip = null)
                            },
                        ) {
                            ModelNode(modelInstance = instance)
                        }
                    }
                }
            }
        }
    }
}

/** То, что пишет кадровый колбэк ARCore. Не state: перерисовка от этого не нужна. */
private class TrackingMemory {
    var markerPose: MarkerPose? = null
    var placedInFront = false
    var trackingSinceNanos = 0L
    var cameraState: TrackingState? = null
    var intrinsicsReported = false
    var measuredWidthMeters: Float? = null
    var loggedWidthMeters = 0f
    var database: Pair<Session, AugmentedImageDatabase>? = null
    var lastQrScanNanos = 0L

    /** Код уже прочитан — проводник выходит и остаётся, даже если код убрали из кадра. */
    var qrAccepted = false
}

/** Узлы проводника и их поза на текущий кадр. */
private class CompanionRig {
    var anchor: NodeImpl? = null
    var body: NodeImpl? = null
    var spin: NodeImpl? = null
    var sizer: NodeImpl? = null
    var placement: CompanionPlacement? = null
    var height: Float = DEFAULT_COMPANION_HEIGHT_METERS

    fun update(frameTimeNanos: Long, flip: FlipTransform?) {
        val current = placement ?: return
        val pivot = height * SPIN_PIVOT
        anchor?.apply {
            position = current.position.toPosition()
            rotation = Rotation(y = current.yawDegrees.toFloat())
        }
        val breath = if (flip == null) {
            sin(frameTimeNanos / 1_000_000.0 / BREATH_PERIOD_MILLIS * TWO_PI).toFloat() * BREATH_AMPLITUDE
        } else {
            0f
        }
        body?.apply {
            position = Position(y = (flip?.liftFraction ?: 0f) * height * FLIP_LIFT)
            scale = Scale(flip?.scaleX ?: 1f, (flip?.scaleY ?: 1f) + breath, flip?.scaleX ?: 1f)
        }
        spin?.apply {
            position = Position(y = pivot)
            rotation = Rotation(x = flip?.rotationDegrees ?: 0f)
        }
        sizer?.apply {
            position = Position(y = -pivot)
            scale = Scale(height)
        }
    }
}

/**
 * Картинка маркера, уменьшенная до [MARKER_MAX_SIDE_PX] по большей стороне.
 *
 * Больше ARCore не нужно: распознаёт он не хуже, а перевод в оттенки серого
 * идёт попиксельно, и каждый лишний пиксель — лишнее время до первого трекинга.
 * Уменьшение степенью двойки через inSampleSize — прямо при декодировании,
 * без полноразмерной копии в памяти.
 */
private fun decodeMarker(assets: AssetManager, path: String): Bitmap? = runCatching {
    val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    assets.open(path).use { BitmapFactory.decodeStream(it, null, bounds) }
    val options = BitmapFactory.Options().apply {
        inSampleSize = sampleSizeFor(bounds.outWidth, bounds.outHeight, MARKER_MAX_SIDE_PX)
        // ARCore принимает только ARGB_8888.
        inPreferredConfig = Bitmap.Config.ARGB_8888
    }
    assets.open(path).use { BitmapFactory.decodeStream(it, null, options) }
}.onFailure { Log.e(TAG, "Маркер $path не прочитан", it) }.getOrNull()

/**
 * Во сколько раз уменьшить картинку при декодировании.
 *
 * Степень двойки — такую понимает inSampleSize. Большая сторона после
 * уменьшения остаётся не меньше [maxSide]: мельче ARCore узнаёт хуже.
 */
internal fun sampleSizeFor(width: Int, height: Int, maxSide: Int): Int {
    var sample = 1
    while (maxOf(width, height) / (sample * 2) >= maxSide) sample *= 2
    return sample
}

private fun AugmentedImage.toMarkerPose(): MarkerPose {
    val pose = centerPose
    return MarkerPose(
        center = Vec3(pose.tx().toDouble(), pose.ty().toDouble(), pose.tz().toDouble()),
        normal = pose.yAxis.toVec3(),
        towardBottom = pose.zAxis.toVec3(),
        heightMeters = extentZ.toDouble(),
    )
}

private fun FloatArray.toVec3() = Vec3(this[0].toDouble(), this[1].toDouble(), this[2].toDouble())

private fun Vec3.toPosition() = Position(x.toFloat(), y.toFloat(), z.toFloat())

/** Имя картинки в базе ARCore. Маркер на экране один, имя служебное. */
private const val MARKER_NAME = "point-marker"

/** Большая сторона картинки маркера после уменьшения, пиксели. */
private const val MARKER_MAX_SIDE_PX = 800

/** На каком расстоянии от камеры встаёт проводник, если таблички нет. */
/**
 * На каком расстоянии ставить проводника перед человеком, метры.
 *
 * Ростом с ребёнка и в двух шагах — фигура целиком помещается в кадр и её
 * видно. Ближе она упирается в край экрана и читается как обрезок текстуры.
 */
private const val IN_FRONT_DISTANCE_METERS = 1.8

/**
 * Как часто искать QR в кадре, мс.
 *
 * Декодер работает в кадровом колбэке сессии, и гонять его сорок раз в секунду
 * — верный способ получить рывки картинки. Четырёх проверок в секунду хватает:
 * человек подносит код и держит его дольше.
 */
private const val QR_SCAN_INTERVAL_MILLIS = 250L

/** Высота оси оборота в долях роста — примерно пояс. */
private const val SPIN_PIVOT = 0.5f

/** Высота подскока в сальто в долях роста. */
private const val FLIP_LIFT = 0.6f

private const val BREATH_PERIOD_MILLIS = 2600.0
private const val BREATH_AMPLITUDE = 0.012f
private const val TWO_PI = 2.0 * Math.PI

private const val TAG = "ArMarkerScene"
