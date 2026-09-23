package ru.marshruty.ar.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import ru.marshruty.ar.data.MediaPlayerNarration
import ru.marshruty.ar.data.NarrationSound
import ru.marshruty.ar.domain.narrationAudioOf

/**
 * Озвучка точки, живущая ровно столько, сколько открыт экран.
 *
 * `null` — озвучки нет: её не прислали или строка пустая. Экран от этого не
 * меняется, субтитры идут по своим часам.
 *
 * Свернули приложение — рассказ замолкает: голос из кармана посреди улицы
 * человек не просил. Вернулись — продолжается с того же места, если до этого
 * звучал.
 */
@Composable
internal fun rememberNarrationSound(audioUri: String?): NarrationSound? {
    val context = LocalContext.current
    val sound = remember(audioUri) {
        narrationAudioOf(audioUri)?.let { MediaPlayerNarration(context, it) }
    }

    val lifecycleOwner = LocalLifecycleOwner.current
    DisposableEffect(sound, lifecycleOwner) {
        if (sound == null) return@DisposableEffect onDispose { }

        var playedBeforePause = false
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_PAUSE -> {
                    playedBeforePause = sound.isPlaying
                    sound.pause()
                }
                Lifecycle.Event.ON_RESUME -> if (playedBeforePause) sound.play()
                else -> Unit
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            sound.release()
        }
    }

    return sound
}
