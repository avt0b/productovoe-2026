package ru.marshruty.ar.ui

import android.content.res.AssetManager
import android.graphics.BitmapFactory
import android.util.Log
import androidx.compose.foundation.Image
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import ru.marshruty.ar.domain.CompanionAction
import ru.marshruty.ar.domain.FlipTransform
import ru.marshruty.ar.domain.SpriteClip

/**
 * Покадровый персонаж из ассетов.
 *
 * Кадры лежат в `assets/<папка>/` и называются по образцу
 * `idle_000.png`, `talking_000.png`, `trick_000.png`. Порядок — по имени,
 * поэтому нумерация должна быть с ведущими нулями.
 *
 * Одного файла `idle_000.png` достаточно, чтобы персонаж появился: статичная
 * картинка — это клип из одного кадра. Так можно за минуту подставить любую
 * модель и посмотреть, как она смотрится в кадре, не рисуя анимацию.
 *
 * Если папки нет или она пуста — рисуется заглушка, экран не падает.
 */
data class CompanionFrames(
    val frames: Map<CompanionAction, List<ImageBitmap>> = emptyMap(),
    val fps: Int = 12,
) {
    val isEmpty: Boolean get() = frames.values.all { it.isEmpty() }

    /** Клип действия или подстановка ближайшего доступного. */
    fun clipFor(action: CompanionAction): SpriteClip? {
        val list = frames[action]?.takeIf { it.isNotEmpty() }
            ?: frames[CompanionAction.IDLE]?.takeIf { it.isNotEmpty() }
            ?: return null
        return SpriteClip(
            frameCount = list.size,
            fps = fps,
            loop = action != CompanionAction.TRICK,
        )
    }

    /** Есть ли собственные кадры именно у этого действия. */
    fun has(action: CompanionAction): Boolean = frames[action]?.isNotEmpty() == true

    /**
     * Клип трюка.
     *
     * Если кадров трюка нет — возвращается тайминг по умолчанию: сальто тогда
     * играется трансформацией (поворот с подскоком), а не картинками, и потому
     * работает с любым персонажем, включая 3D-модель без анимаций внутри.
     */
    fun trickClip(): SpriteClip =
        frames[CompanionAction.TRICK]?.takeIf { it.isNotEmpty() }
            ?.let { SpriteClip(frameCount = it.size, fps = fps, loop = false) }
            ?: SpriteClip.DefaultTrick

    fun frame(action: CompanionAction, index: Int): ImageBitmap? {
        val list = frames[action]?.takeIf { it.isNotEmpty() }
            ?: frames[CompanionAction.IDLE]?.takeIf { it.isNotEmpty() }
            ?: return null
        return list.getOrNull(index.coerceIn(0, list.lastIndex))
    }
}

/** Загружает кадры один раз при открытии экрана. */
@Composable
fun rememberCompanionFrames(assetFolder: String, fps: Int = 12): CompanionFrames {
    val context = LocalContext.current
    var loaded by remember(assetFolder) { mutableStateOf(CompanionFrames(fps = fps)) }

    LaunchedEffect(assetFolder) {
        loaded = withContext(Dispatchers.IO) {
            CompanionFrames(loadFrames(context.assets, assetFolder), fps)
        }
    }
    return loaded
}

private fun loadFrames(assets: AssetManager, folder: String): Map<CompanionAction, List<ImageBitmap>> {
    // Пустая строка — это корень `assets`, и перебирать его целиком нельзя:
    // туда попадут чужие файлы, включая саму 3D-модель.
    if (folder.isBlank()) return emptyMap()

    val names = runCatching { assets.list(folder)?.toList().orEmpty() }
        .onFailure { Log.i(TAG, "Папка ассетов '$folder' не найдена — покажем заглушку") }
        .getOrDefault(emptyList())
        .filter { it.endsWith(".png", true) || it.endsWith(".webp", true) }
        .sorted()

    if (names.isEmpty()) return emptyMap()

    return names
        .groupBy { name -> actionOf(name) }
        .mapNotNull { (action, files) ->
            if (action == null) return@mapNotNull null
            val bitmaps = files.mapNotNull { file ->
                runCatching {
                    assets.open("$folder/$file").use { stream ->
                        BitmapFactory.decodeStream(stream)?.asImageBitmap()
                    }
                }.onFailure { Log.w(TAG, "Кадр '$file' не прочитан", it) }.getOrNull()
            }
            if (bitmaps.isEmpty()) null else action to bitmaps
        }
        .toMap()
}

/** Действие определяется префиксом имени файла до подчёркивания. */
private fun actionOf(fileName: String): CompanionAction? =
    when (fileName.substringBefore('_').lowercase()) {
        "idle" -> CompanionAction.IDLE
        "talking", "talk" -> CompanionAction.TALKING
        "trick", "flip" -> CompanionAction.TRICK
        else -> null
    }

/**
 * Текущий кадр персонажа.
 *
 * [flip] задан, когда сальто играется трансформацией, а не кадрами: тогда
 * картинка проворачивается и подпрыгивает. Точка вращения смещена ниже центра —
 * персонаж стоит на земле, и крутиться он должен вокруг пояса, а не вокруг лба.
 */
@Composable
fun SpriteArtwork(
    frames: CompanionFrames,
    action: CompanionAction,
    frameIndex: Int,
    modifier: Modifier = Modifier,
    flip: FlipTransform? = null,
) {
    val posed = if (flip == null) {
        modifier
    } else {
        modifier.graphicsLayer {
            rotationZ = flip.rotationDegrees
            scaleX = flip.scaleX
            scaleY = flip.scaleY
            translationY = -flip.liftFraction * size.height * FLIP_HEIGHT_FRACTION
            transformOrigin = TransformOrigin(0.5f, 0.62f)
        }
    }

    val bitmap = frames.frame(action, frameIndex)
    if (bitmap == null) {
        CompanionPlaceholder(posed)
    } else {
        Image(
            bitmap = bitmap,
            contentDescription = null,
            modifier = posed,
            contentScale = ContentScale.Fit,
        )
    }
}

/** Высота подскока в долях от роста персонажа. */
private const val FLIP_HEIGHT_FRACTION = 0.45f

private const val TAG = "CompanionArtwork"
