package ru.marshruty.ar.data

import kotlinx.coroutines.flow.Flow
import ru.marshruty.ar.domain.CameraFieldOfView
import ru.marshruty.ar.domain.DeviceOrientation
import ru.marshruty.ar.domain.LocationFix

/**
 * Источники данных экрана.
 *
 * Всё, что приходит из железа, спрятано за интерфейсами — не ради красоты,
 * а чтобы экран можно было прогонять по записанному сценарию: в Preview,
 * в тестах и на защите, где нет ни неба, ни GPS.
 */

/** Куда направлена камера. */
interface OrientationSource {
    val orientation: Flow<DeviceOrientation>

    /** Компас требует калибровки «восьмёркой» — об этом надо сказать вслух. */
    val needsCalibration: Flow<Boolean>
}

/** Где находится наблюдатель. `null` — фикса ещё нет. */
interface LocationSource {
    val fix: Flow<LocationFix?>
}

/** Углы обзора активной камеры. */
interface OpticsSource {
    suspend fun fieldOfView(): CameraFieldOfView
}
