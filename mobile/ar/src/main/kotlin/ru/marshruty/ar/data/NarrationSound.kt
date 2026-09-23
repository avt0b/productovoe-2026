package ru.marshruty.ar.data

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.media.MediaPlayer
import android.net.Uri
import android.os.SystemClock
import android.util.Log
import ru.marshruty.ar.domain.NarrationAudio

/**
 * Звучащий рассказ проводника.
 *
 * Экран спрашивает позицию и ничего не знает о том, откуда она взялась.
 * `null` в [positionMillis] значит «звука нет» — и это штатный ответ, а не
 * поломка: озвучку для точки могли не записать, файл мог не открыться, связь
 * могла пропасть. Экран в таком случае ведёт субтитры по своим часам.
 */
interface NarrationSound {
    /** Позиция звука, мс. `null` — звука нет, время придётся считать самому. */
    val positionMillis: Long?

    /** Человек хочет слушать: рассказ не на паузе и не доигран. */
    val isPlaying: Boolean

    /** Рассказ доигран до конца. */
    val isFinished: Boolean

    fun play()

    fun pause()

    /** С начала: «Повторить» на панели проводника. */
    fun replay()

    fun setMuted(muted: Boolean)

    fun release()
}

private const val TAG = "ArNarration"

/**
 * Сколько ждать подготовки, мс.
 *
 * Пока плеер готовится, экран держит субтитры на первой строке: иначе они
 * уйдут вперёд и голос начнёт отставать с первой же секунды. Но ждать вечно
 * нельзя — файл может не открыться и без ошибки (сеть висит), а рассказ
 * должен идти. Десяти секунд хватает и на локальный файл, и на загрузку по
 * мобильному интернету в поле.
 */
private const val PREPARE_TIMEOUT_MILLIS = 10_000L

/** Громкость рассказа, когда поверх него говорит навигатор или будильник. */
private const val DUCKED_VOLUME = 0.2f

/**
 * Рассказ на системном `MediaPlayer`.
 *
 * Своего движка звука модулю не нужно: одна дорожка, без перемотки по
 * таймлайну и без эффектов. `MediaPlayer` есть в любом Android и не тянет
 * зависимостей — APK экскурсии не станет тяжелее ни на килобайт.
 */
internal class MediaPlayerNarration(
    context: Context,
    private val audio: NarrationAudio,
) : NarrationSound {

    private enum class State { PREPARING, READY, FINISHED, FAILED }

    private val appContext = context.applicationContext
    private val audioManager = appContext.getSystemService(Context.AUDIO_SERVICE) as? AudioManager

    private var state = State.PREPARING
    private var preparingSince = SystemClock.elapsedRealtime()

    /** Намерение человека, а не состояние плеера: до подготовки играть нечему. */
    private var wantsToPlay = false
    private var muted = false
    private var ducked = false
    private var releasing = false

    private var player: MediaPlayer? = null

    private val focusRequest: AudioFocusRequest =
        AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    // Речь, а не музыка: система выберет для неё свою обработку.
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build(),
            )
            .setOnAudioFocusChangeListener(::onFocusChange)
            .build()

    private var hasFocus = false

    init {
        runCatching { openPlayer() }
            .onFailure { failed("Озвучка не открылась: ${it.message}") }
    }

    private fun openPlayer() {
        val created = MediaPlayer().apply {
            setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build(),
            )
            when (audio) {
                is NarrationAudio.Asset -> appContext.assets.openFd(audio.path).use { descriptor ->
                    setDataSource(descriptor.fileDescriptor, descriptor.startOffset, descriptor.length)
                }
                is NarrationAudio.Uri -> setDataSource(appContext, Uri.parse(audio.value))
            }
            setOnPreparedListener {
                state = State.READY
                applyVolume()
                if (wantsToPlay) startPlayback()
            }
            setOnCompletionListener {
                state = State.FINISHED
                abandonFocus()
            }
            setOnErrorListener { _, what, extra ->
                failed("Плеер озвучки отдал ошибку what=$what extra=$extra")
                // true — ошибку разобрали сами, плеер не должен звать её ещё раз.
                true
            }
            prepareAsync()
        }
        player = created
    }

    private fun failed(message: String) {
        Log.i(TAG, "$message. Рассказ пойдёт субтитрами.")
        state = State.FAILED
        abandonFocus()
        runCatching { player?.release() }
        player = null
    }

    override val positionMillis: Long?
        get() = when (state) {
            // Ждём голос — держим субтитры на первой строке, но не дольше таймаута.
            State.PREPARING ->
                if (SystemClock.elapsedRealtime() - preparingSince > PREPARE_TIMEOUT_MILLIS) {
                    failed("Озвучка не подготовилась за ${PREPARE_TIMEOUT_MILLIS / 1000} с")
                    null
                } else {
                    0L
                }
            // После конца дорожки currentPosition у MediaPlayer непредсказуем.
            State.FINISHED -> player?.duration?.toLong() ?: 0L
            State.READY -> runCatching { player?.currentPosition?.toLong() }.getOrNull()
            State.FAILED -> null
        }

    override val isPlaying: Boolean
        get() = wantsToPlay && state != State.FINISHED && state != State.FAILED

    override val isFinished: Boolean
        get() = state == State.FINISHED

    override fun play() {
        wantsToPlay = true
        if (state == State.READY) startPlayback()
    }

    private fun startPlayback() {
        if (!requestFocus()) {
            // Фокус не дали — звучать поверх чужого разговора нельзя.
            wantsToPlay = false
            return
        }
        runCatching { player?.start() }
            .onFailure { failed("Плеер не запустился: ${it.message}") }
    }

    override fun pause() {
        wantsToPlay = false
        runCatching { if (player?.isPlaying == true) player?.pause() }
        abandonFocus()
    }

    override fun replay() {
        when (state) {
            State.FAILED -> return
            State.FINISHED -> state = State.READY
            else -> Unit
        }
        runCatching { player?.seekTo(0) }
        play()
    }

    override fun setMuted(muted: Boolean) {
        this.muted = muted
        applyVolume()
    }

    private fun applyVolume() {
        val volume = when {
            muted -> 0f
            ducked -> DUCKED_VOLUME
            else -> 1f
        }
        runCatching { player?.setVolume(volume, volume) }
    }

    override fun release() {
        releasing = true
        abandonFocus()
        runCatching { player?.release() }
        player = null
        state = State.FAILED
    }

    private fun requestFocus(): Boolean {
        if (hasFocus) return true
        val manager = audioManager ?: return true
        hasFocus = manager.requestAudioFocus(focusRequest) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        return hasFocus
    }

    private fun abandonFocus() {
        if (!hasFocus) return
        audioManager?.abandonAudioFocusRequest(focusRequest)
        hasFocus = false
    }

    /**
     * Звонок, навигатор, будильник.
     *
     * Насовсем фокус отняли — рассказ встаёт на паузу и сам не продолжится:
     * человек вернётся и нажмёт. На время — продолжаем с того же места, это
     * привычное поведение любого плеера.
     */
    private fun onFocusChange(change: Int) {
        if (releasing) return
        when (change) {
            AudioManager.AUDIOFOCUS_LOSS -> {
                hasFocus = false
                pause()
            }
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT -> {
                runCatching { if (player?.isPlaying == true) player?.pause() }
            }
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK -> {
                ducked = true
                applyVolume()
            }
            AudioManager.AUDIOFOCUS_GAIN -> {
                ducked = false
                applyVolume()
                if (wantsToPlay && state == State.READY) runCatching { player?.start() }
            }
        }
    }
}
