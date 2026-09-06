package ru.marshruty.ar

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import ru.marshruty.ar.domain.GeoPoint
import ru.marshruty.ar.ui.cardinal
import ru.marshruty.ar.ui.formatCoordinates

class NarrationTest {

    private val lines = listOf(
        SubtitleLine(0, 3_000, "первая"),
        SubtitleLine(3_000, 6_000, "вторая"),
        SubtitleLine(8_000, 10_000, "третья после паузы"),
    )

    @Test
    fun `выбирается строка, звучащая в данный момент`() {
        assertEquals("первая", lines.lineAt(1_500)?.text)
        assertEquals("вторая", lines.lineAt(4_000)?.text)
        assertEquals("третья после паузы", lines.lineAt(9_999)?.text)
    }

    @Test
    fun `на стыке строк берётся следующая, а не предыдущая`() {
        assertEquals("вторая", lines.lineAt(3_000)?.text)
    }

    @Test
    fun `в паузе и за пределами дорожки строки нет`() {
        assertNull(lines.lineAt(7_000))
        assertNull(lines.lineAt(20_000))
        assertNull(emptyList<SubtitleLine>().lineAt(0))
    }

    @Test(expected = IllegalArgumentException::class)
    fun `строка с концом раньше начала отвергается`() {
        SubtitleLine(fromMillis = 5_000, toMillis = 1_000, text = "битая")
    }

    @Test
    fun `шаг маршрута вне диапазона отвергается`() {
        val base = { index: Int ->
            ArPointSpec(
                pointId = "p", title = "т", stepIndex = index, stepTotal = 4,
                target = null, companion = null,
                narration = NarrationSpec(audioUri = null, subtitles = emptyList()),
            )
        }
        assertEquals(0.5f, base(2).progress, 0.001f)
        runCatching { base(0) }.let { assertTrue("шаг 0 должен падать", it.isFailure) }
        runCatching { base(5) }.let { assertTrue("шаг 5 из 4 должен падать", it.isFailure) }
    }

    @Test
    fun `румб считается по азимуту`() {
        assertEquals("С", cardinal(0.0))
        assertEquals("СВ", cardinal(45.0))
        assertEquals("В", cardinal(90.0))
        assertEquals("ЮЗ", cardinal(225.0))
        assertEquals("СЗ", cardinal(315.0))
        // Переход через круг не должен выходить за пределы таблицы.
        assertEquals("С", cardinal(359.0))
        assertEquals("С", cardinal(-1.0))
    }

    @Test
    fun `координаты форматируются в градусы-минуты-секунды с полушарием`() {
        val text = formatCoordinates(52.97012, 36.06673)

        assertTrue("получили '$text'", text.startsWith("52°58'"))
        assertTrue("получили '$text'", text.contains("N"))
        assertTrue("получили '$text'", text.contains("36°04'"))
        assertTrue("получили '$text'", text.endsWith("E"))
    }

    @Test
    fun `южное и западное полушария помечаются корректно`() {
        val text = formatCoordinates(-33.8688, -151.2093)

        assertTrue("получили '$text'", text.contains("S"))
        assertTrue("получили '$text'", text.contains("W"))
    }

    @Test
    fun `сценарий симуляции целится ровно в цель`() {
        val bearing = ru.marshruty.ar.domain.bearingDegrees(
            GeoPoint(52.9700, 36.0665),
            GeoPoint(52.97012, 36.06673),
        )
        assertEquals(bearing, ru.marshruty.ar.sim.Simulation.bearingToTarget, 0.001)
    }
}
