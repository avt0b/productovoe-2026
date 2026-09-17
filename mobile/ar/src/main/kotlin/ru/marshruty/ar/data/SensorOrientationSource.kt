package ru.marshruty.ar.data

import android.content.Context
import android.hardware.GeomagneticField
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.conflate
import ru.marshruty.ar.domain.DeviceOrientation
import ru.marshruty.ar.domain.GeoPoint
import ru.marshruty.ar.domain.OrientationFilter
import ru.marshruty.ar.domain.applyDeclination

/**
 * Ориентация камеры по датчику вращения.
 *
 * `TYPE_ROTATION_VECTOR` — уже сведённые гироскоп, акселерометр и магнитометр:
 * стабильнее, чем считать это самому из сырых показаний.
 *
 * Три вещи, без которых наведение не работает:
 *
 * 1. **Пересчёт осей.** Датчик описывает положение экрана, а нам нужно
 *    направление объектива. `remapCoordinateSystem(AXIS_X, AXIS_Z)` разворачивает
 *    систему так, что азимут становится направлением камеры при вертикально
 *    удерживаемом телефоне.
 * 2. **Магнитное склонение.** Датчик даёт магнитный север, `bearingDegrees` —
 *    истинный. В Орловской области расхождение около +9°.
 * 3. **Сглаживание.** Сырой азимут дрожит на несколько градусов даже в покое.
 *
 * Экран заблокирован в портретной ориентации: при повороте устройства
 * пересчёт осей был бы другим.
 */
class SensorOrientationSource(
    context: Context,
    private val locationProvider: () -> GeoPoint?,
    smoothing: Double = 0.15,
) : OrientationSource {

    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val rotationSensor: Sensor? = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)

    private val azimuthFilter = OrientationFilter(smoothing)
    private val calibration = MutableStateFlow(false)

    /** Датчика вращения может не быть — хост тогда покажет обычную карточку точки. */
    val isAvailable: Boolean get() = rotationSensor != null

    override val needsCalibration: Flow<Boolean> = calibration

    override val orientation: Flow<DeviceOrientation> = callbackFlow {
        val sensor = rotationSensor
        if (sensor == null) {
            close()
            return@callbackFlow
        }

        val rotationMatrix = FloatArray(9)
        val remapped = FloatArray(9)
        val angles = FloatArray(3)

        val listener = object : SensorEventListener {
            override fun onSensorChanged(event: SensorEvent) {
                SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values)
                // Ось Y после пересчёта смотрит туда же, куда объектив.
                SensorManager.remapCoordinateSystem(
                    rotationMatrix,
                    SensorManager.AXIS_X,
                    SensorManager.AXIS_Z,
                    remapped,
                )
                SensorManager.getOrientation(remapped, angles)

                val magneticAzimuth = Math.toDegrees(angles[0].toDouble())
                val trueAzimuth = applyDeclination(magneticAzimuth, declinationDegrees())

                trySend(
                    DeviceOrientation(
                        azimuthDegrees = azimuthFilter.update(trueAzimuth),
                        // Знак выбран так, чтобы «камера смотрит вверх» давало
                        // положительный угол — этого ждёт projectToScreen.
                        pitchDegrees = -Math.toDegrees(angles[1].toDouble()),
                    ),
                )
            }

            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
                calibration.value = accuracy == SensorManager.SENSOR_STATUS_ACCURACY_LOW ||
                    accuracy == SensorManager.SENSOR_STATUS_UNRELIABLE
            }
        }

        // SENSOR_DELAY_GAME — примерно 50 Гц: плавно и без лишнего расхода батареи.
        sensorManager.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_GAME)
        awaitClose { sensorManager.unregisterListener(listener) }
    }.conflate() // экран рисуется реже, чем тикает датчик

    /**
     * Склонение считается по текущим координатам. Пока фикса нет, берём
     * значение для Орла — ошибиться на пару градусов лучше, чем на девять.
     */
    private fun declinationDegrees(): Double {
        val point = locationProvider() ?: return OREL_FALLBACK_DECLINATION
        return GeomagneticField(
            point.latitude.toFloat(),
            point.longitude.toFloat(),
            0f,
            System.currentTimeMillis(),
        ).declination.toDouble()
    }

    private companion object {
        const val OREL_FALLBACK_DECLINATION = 9.0
    }
}
