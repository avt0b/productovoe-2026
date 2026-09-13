package ru.marshruty.ar.domain

import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.sqrt

/** Что сейчас с маркером — для подсказки на экране. */
enum class MarkerStatus {
    /** Маркер ещё ни разу не найден. */
    SEARCHING,

    /** Картинка в кадре, поза свежая. */
    TRACKING,

    /** Картинка ушла из кадра, но ARCore держит мир — проводник стоит где стоял. */
    HOLDING,

    /** ARCore потерял окружение: резкое движение, темнота, голая стена. */
    LOST,

    /** Картинка не годится в маркер: ARCore не нашёл на ней за что зацепиться. */
    BAD_MARKER,

    /** Таблички не нашлось за отведённое время — проводник поставлен перед камерой. */
    IN_FRONT,
}

/** Вектор в мировых координатах ARCore: Y вверх, метры. */
data class Vec3(val x: Double, val y: Double, val z: Double) {
    operator fun plus(other: Vec3) = Vec3(x + other.x, y + other.y, z + other.z)
    operator fun minus(other: Vec3) = Vec3(x - other.x, y - other.y, z - other.z)
    operator fun times(k: Double) = Vec3(x * k, y * k, z * k)

    val length: Double get() = sqrt(x * x + y * y + z * z)

    fun normalized(): Vec3 = if (length < 1e-9) this else this * (1.0 / length)

    /** Проекция на пол: без вертикальной составляющей. */
    fun horizontal(): Vec3 = Vec3(x, 0.0, z)
}

/**
 * Поза найденной картинки в мире ARCore.
 *
 * Оси — как их отдаёт ARCore для AugmentedImage: Y — нормаль, смотрит из
 * картинки наружу, Z — вдоль картинки к её нижнему краю.
 */
data class MarkerPose(
    val center: Vec3,
    val normal: Vec3,
    val towardBottom: Vec3,
    /** Высота картинки вдоль её оси Z, метры. */
    val heightMeters: Double,
)

/** Как висит картинка: лежит на столе или земле — или висит на стене. */
enum class MarkerOrientation { LYING, STANDING }

data class CompanionPlacement(
    val position: Vec3,
    /** Поворот вокруг вертикали, градусы 0..360: 0 — лицом к +Z мира. */
    val yawDegrees: Double,
    val orientation: MarkerOrientation,
)

/**
 * Граница между «лежит» и «висит»: нормаль ближе к вертикали, чем к горизонту.
 * Это 45°, и порог не случаен: табличку на пюпитре под 30° человек считает
 * лежащей, а плакат на стене с небольшим завалом — висящим.
 */
private const val LYING_COS = 0.7071

/** Отступ от стены: без него ноги проводника проваливаются в плакат. */
private const val WALL_CLEARANCE_METERS = 0.04

/** Меньше сантиметра по горизонтали — направление не определено. */
private const val MIN_HORIZONTAL_METERS = 0.01

/**
 * Куда поставить проводника относительно найденной картинки.
 *
 * Персонаж всегда стоит вертикально по гравитации, а не по картинке: если
 * повернуть его вместе с плакатом на стене, он будет торчать из стены боком.
 * Лежащая картинка — он стоит прямо на ней. Висящая — стоит у нижнего края,
 * как на полочке под табличкой.
 *
 * Лицом он поворачивается к человеку: это проводник, он с ним разговаривает.
 */
fun placeCompanion(marker: MarkerPose, camera: Vec3): CompanionPlacement {
    val normal = marker.normal.normalized()
    val orientation = if (abs(normal.y) >= LYING_COS) MarkerOrientation.LYING else MarkerOrientation.STANDING

    val position = when (orientation) {
        MarkerOrientation.LYING -> marker.center
        MarkerOrientation.STANDING ->
            marker.center +
                marker.towardBottom.normalized() * (marker.heightMeters / 2) +
                normal.horizontal().normalized() * WALL_CLEARANCE_METERS
    }

    // Камера ровно над персонажем — горизонтального направления нет. Тогда
    // лицом туда, откуда на такую картинку обычно смотрят.
    val usualViewer = when (orientation) {
        MarkerOrientation.LYING -> marker.towardBottom
        MarkerOrientation.STANDING -> normal
    }
    val yaw = yawToward(camera - position) ?: yawToward(usualViewer) ?: 0.0

    return CompanionPlacement(position, normalizeDegrees(yaw), orientation)
}

/**
 * Поза «воображаемой таблички» перед камерой — когда настоящей не нашлось.
 *
 * Ставится по лучу взгляда, а не по горизонту: телефон обычно держат с наклоном
 * вниз, и персонаж на уровне глаз оказался бы над кадром. Центр опущен на
 * полроста, чтобы в середине кадра был пояс, а не ноги.
 */
fun poseInFrontOfCamera(
    eye: Vec3,
    forward: Vec3,
    distanceMeters: Double,
    companionHeightMeters: Double,
): MarkerPose = MarkerPose(
    center = eye + forward.normalized() * distanceMeters - Vec3(0.0, companionHeightMeters / 2, 0.0),
    normal = Vec3(0.0, 1.0, 0.0),
    // «Низ» воображаемой таблички смотрит на человека — лицом к нему и встанет.
    towardBottom = forward.horizontal().normalized() * -1.0,
    heightMeters = 0.0,
)

/** Поворот вокруг вертикали, при котором ось +Z модели смотрит вдоль [direction]. */
internal fun yawToward(direction: Vec3): Double? {
    val flat = direction.horizontal()
    if (flat.length < MIN_HORIZONTAL_METERS) return null
    return Math.toDegrees(atan2(flat.x, flat.z))
}

/**
 * Сглаживание позы проводника между кадрами.
 *
 * ARCore уточняет позу картинки каждый кадр, и сырая поза дрожит на
 * миллиметры. На персонаже ростом 30 см это видно как тряска. Экспоненциальное
 * сглаживание дрожь гасит, но настоящий перенос пропускает: если маркер
 * переставили дальше [jumpMeters], персонаж перепрыгивает сразу, а не ползёт
 * через весь стол на глазах у пользователя.
 *
 * Поворот сглаживается сильнее позиции: так он читается как «обернулся»,
 * а не как дёрганье за каждым движением руки.
 */
class PlacementSmoother(
    private val positionFactor: Double = 0.25,
    private val yawFactor: Double = 0.12,
    private val jumpMeters: Double = 0.5,
) {
    var current: CompanionPlacement? = null
        private set

    fun update(target: CompanionPlacement): CompanionPlacement {
        val previous = current
        val next = if (previous == null || (target.position - previous.position).length > jumpMeters) {
            target
        } else {
            val turn = angleDeltaDegrees(previous.yawDegrees, target.yawDegrees) * yawFactor
            CompanionPlacement(
                position = previous.position + (target.position - previous.position) * positionFactor,
                yawDegrees = normalizeDegrees(previous.yawDegrees + turn),
                orientation = target.orientation,
            )
        }
        current = next
        return next
    }

    fun reset() {
        current = null
    }
}

/** Во сколько раз проводник выше ширины таблички: стоит на ней и чуть над ней возвышается. */
private const val HEIGHT_PER_MARKER_WIDTH = 1.1f

/** Рост, пока табличка не найдена и мерить нечего, — ребёнку по колено, в кадре не теряется. */
const val DEFAULT_COMPANION_HEIGHT_METERS = 0.35f

/** Измерение ARCore меньше двух сантиметров — это ещё не оценка, а шум первых кадров. */
private const val MIN_MEASURED_WIDTH_METERS = 0.02f

/**
 * Рост проводника в метрах.
 *
 * Приоритет: явно заданный рост, затем от известной ширины таблички, затем от
 * ширины, которую измерил ARCore, и только потом значение по умолчанию.
 */
fun companionHeightFor(
    explicitMeters: Float?,
    knownWidthMeters: Float?,
    measuredWidthMeters: Float?,
): Float {
    val width = knownWidthMeters ?: measuredWidthMeters?.takeIf { it >= MIN_MEASURED_WIDTH_METERS }
    return explicitMeters ?: width?.times(HEIGHT_PER_MARKER_WIDTH) ?: DEFAULT_COMPANION_HEIGHT_METERS
}
