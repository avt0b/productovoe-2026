package ru.marshruty.ar.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import ru.marshruty.ar.SubtitleLine
import ru.marshruty.ar.durationMillis
import ru.marshruty.ar.lineAt

class SubtitleFitTest {

    /** Нарезка «на глаз»: хост дал каждой строке по шесть секунд. */
    private val estimated = listOf(
        SubtitleLine(0, 6_000, "Здесь держали рубеж связисты сорок первого стрелкового полка, и держали до последнего."),
        SubtitleLine(6_000, 12_000, "Они тянули провод под огнём."),
        SubtitleLine(12_000, 18_000, "Найдём след окопа!"),
    )

    @Test
    fun `подогнанные субтитры кончаются ровно на конце записи`() {
        val fitted = estimated.fittedTo(42_000)

        assertEquals(42_000L, fitted.durationMillis())
        assertEquals(0L, fitted.first().fromMillis)
    }

    @Test
    fun `длинной строке достаётся больше времени, чем короткой`() {
        val fitted = estimated.fittedTo(42_000)

        val long = fitted[0].toMillis - fitted[0].fromMillis
        val short = fitted[2].toMillis - fitted[2].fromMillis
        assertTrue("длинная $long мс, короткая $short мс", long > short * 2)
    }

    @Test
    fun `строки идут подряд и не перекрываются`() {
        val fitted = estimated.fittedTo(42_000)

        fitted.zipWithNext { current, next ->
            assertEquals(current.toMillis, next.fromMillis)
            assertTrue("строка ${current.text} пустая по времени", current.toMillis > current.fromMillis)
        }
        // На любой момент записи есть что показать: пауз в оценке быть не должно.
        listOf(0L, 5_000L, 20_000L, 41_999L).forEach { position ->
            assertNotNull("на $position мс строки нет", fitted.lineAt(position))
        }
    }

    @Test
    fun `текст субтитров не меняется`() {
        val fitted = estimated.fittedTo(42_000)

        assertEquals(estimated.map { it.text }, fitted.map { it.text })
    }

    @Test
    fun `без известной длительности субтитры остаются прежними`() {
        assertEquals(estimated, estimated.fittedTo(0))
        assertEquals(estimated, estimated.fittedTo(-1))
        assertEquals(emptyList<SubtitleLine>(), emptyList<SubtitleLine>().fittedTo(42_000))
    }

    @Test
    fun `запись короче, чем строк, не растягивается`() {
        // Такой записи не бывает, но и падать на ней экран не должен.
        assertEquals(estimated, estimated.fittedTo(2))
    }

    @Test
    fun `одна строка занимает всю запись целиком`() {
        val single = listOf(SubtitleLine(0, 6_000, "Одна фраза"))

        assertEquals(listOf(SubtitleLine(0, 31_000, "Одна фраза")), single.fittedTo(31_000))
    }
}
