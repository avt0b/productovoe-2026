package ru.marshruty.ar;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNull;

import java.util.Collections;
import java.util.List;

import org.junit.Test;

import ru.marshruty.ar.domain.GeoPoint;

/**
 * Контракт глазами хоста.
 *
 * Хост модуля — Capacitor-плагин на Java (`frontend/client`), и умолчания
 * Kotlin оттуда не видны: добавленное поле с умолчанием ломает его сборку, а
 * узнаётся это только при сборке APK, через AAR, через полчаса.
 *
 * Этот тест повторяет вызовы плагина один в один. Он почти ничего не
 * проверяет в рантайме — его работа в том, чтобы не скомпилироваться, если
 * контракт разъехался с хостом.
 */
public class JavaHostContractTest {

    private static List<SubtitleLine> lines() {
        return Collections.singletonList(new SubtitleLine(0L, 6_000L, "Здесь держали рубеж связисты."));
    }

    @Test
    public void рассказ_собирается_без_поля_об_оценке_таймкодов() {
        NarrationSpec narration = new NarrationSpec("https://media.marshruty.ru/clips/7.m4a", lines());

        assertEquals("https://media.marshruty.ru/clips/7.m4a", narration.getAudioUri());
        // Умолчание: таймкоды считаются настоящими, пока хост не сказал обратное.
        assertFalse(narration.getSubtitlesAreEstimated());
    }

    @Test
    public void рассказ_собирается_и_с_нарезкой_на_глаз() {
        NarrationSpec narration = new NarrationSpec(null, lines(), true);

        assertNull(narration.getAudioUri());
        assertEquals(true, narration.getSubtitlesAreEstimated());
    }

    @Test
    public void точка_маршрута_собирается_так_же_как_в_плагине() {
        ArPointSpec spec = new ArPointSpec(
            "wp-2",
            "Рубеж связистов",
            2,
            4,
            new ArTarget(new GeoPoint(52.9706, 36.0672), "След кабельного окопа", 0.0),
            new CompanionSpec("Санитарный пёс Верный", "41-й СП", "companion/verny.glb"),
            new NarrationSpec(null, lines()),
            new MarkerSpec("markers/wp-2.png", 0.30f, null, 4_000L)
        );

        assertEquals("wp-2", spec.getPointId());
        assertEquals(0.5f, spec.getProgress(), 0.001f);
    }
}
