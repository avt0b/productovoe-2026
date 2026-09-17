package ru.marshruty.ar

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SubtitleStabilityTest {

    private val lines = listOf(
        SubtitleLine(500, 6_000, "первая"),
        SubtitleLine(6_000, 12_000, "вторая"),
        // Пауза 12 000..13 000 — тишина между репликами.
        SubtitleLine(13_000, 18_000, "третья"),
    )

    @Test
    fun `стабильная позиция даёт ту же строку, что и живая`() {
        for (position in 0L..20_000L step 7) {
            assertEquals("позиция " + position, lines.lineAt(position), lines.lineAt(lines.stablePositionAt(position)))
        }
    }

    @Test
    fun `позиция меняется только на границах строк`() {
        val distinct = (0L..20_000L step 7).map { lines.stablePositionAt(it) }.toSet()
        // До первой строки, три строки, пауза после второй, конец после третьей.
        assertEquals(setOf(-1L, 500L, 6_000L, 12_000L, 13_000L, 18_000L), distinct)
    }

    @Test
    fun `в паузе строки нет`() {
        assertEquals(null, lines.lineAt(lines.stablePositionAt(12_500)))
    }

    @Test
    fun `пустые субтитры не ломают расчёт`() {
        assertTrue(emptyList<SubtitleLine>().stablePositionAt(5_000) < 0)
    }
}
