package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import ru.marshruty.ar.SubtitleLine
import ru.marshruty.ar.durationMillis
import ru.marshruty.ar.lineAt

class NarrationAudioTest {

    @Test
    fun `asset-ссылка читается как файл в assets, лишние слэши срезаются`() {
        assertEquals(
            NarrationAudio.Asset("narration/wp-2.ogg"),
            narrationAudioOf("asset:///narration/wp-2.ogg"),
        )
        assertEquals(
            NarrationAudio.Asset("narration/wp-2.ogg"),
            narrationAudioOf("asset://narration/wp-2.ogg"),
        )
    }

    @Test
    fun `путь без схемы — тоже ассет`() {
        assertEquals(NarrationAudio.Asset("narration/wp-2.ogg"), narrationAudioOf("narration/wp-2.ogg"))
    }

    @Test
    fun `ссылки и абсолютные пути открывает сам Android`() {
        assertEquals(
            NarrationAudio.Uri("https://media.marshruty.ru/clips/7.m4a"),
            narrationAudioOf("https://media.marshruty.ru/clips/7.m4a"),
        )
        assertEquals(
            NarrationAudio.Uri("file:///data/user/0/ru.marshruty/files/wp-2.ogg"),
            narrationAudioOf("file:///data/user/0/ru.marshruty/files/wp-2.ogg"),
        )
        assertEquals(
            NarrationAudio.Uri("content://ru.marshruty.provider/narration/7"),
            narrationAudioOf("content://ru.marshruty.provider/narration/7"),
        )
        assertEquals(
            NarrationAudio.Uri("/sdcard/Download/wp-2.ogg"),
            narrationAudioOf("/sdcard/Download/wp-2.ogg"),
        )
    }

    @Test
    fun `пустая ссылка — это отсутствие озвучки, а не ошибка`() {
        assertNull(narrationAudioOf(null))
        assertNull(narrationAudioOf(""))
        assertNull(narrationAudioOf("   "))
        // Схема без пути: открывать нечего.
        assertNull(narrationAudioOf("asset:///"))
    }

    @Test
    fun `пока звучит озвучка, время берётся у плеера`() {
        assertEquals(
            4_200L,
            narrationPositionMillis(audioPositionMillis = 4_200, clockMillis = 90_000, startedAtMillis = 0),
        )
    }

    @Test
    fun `без озвучки время идёт от начала рассказа, а не от запуска экрана`() {
        assertEquals(
            5_000L,
            narrationPositionMillis(audioPositionMillis = null, clockMillis = 12_000, startedAtMillis = 7_000),
        )
    }

    @Test
    fun `рассказ, начатый позже текущего кадра, стоит на нуле, а не уходит в минус`() {
        assertEquals(
            0L,
            narrationPositionMillis(audioPositionMillis = null, clockMillis = 1_000, startedAtMillis = 3_000),
        )
    }

    @Test
    fun `длительность рассказа — конец последней строки субтитров`() {
        val lines = listOf(
            SubtitleLine(0, 3_000, "первая"),
            SubtitleLine(3_000, 6_000, "вторая"),
            SubtitleLine(8_000, 10_000, "третья"),
        )

        assertEquals(10_000L, lines.durationMillis())
        // На конце дорожки строки уже нет — по этому признаку экран и молкнет.
        assertNull(lines.lineAt(lines.durationMillis()))
    }

    @Test
    fun `рассказа без субтитров нет и по длительности`() {
        assertEquals(0L, emptyList<SubtitleLine>().durationMillis())
    }
}
