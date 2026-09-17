package ru.marshruty.ar.data

import android.content.Context
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.util.Log
import ru.marshruty.ar.domain.CameraFieldOfView
import ru.marshruty.ar.domain.fieldOfViewFrom

/**
 * Реальные углы обзора основной камеры.
 *
 * Значение по умолчанию (66°) — усреднённое по рынку, и на конкретном телефоне
 * метка из-за него промахивается на несколько градусов. Характеристики
 * объектива читаются один раз при открытии экрана.
 */
class CameraOpticsSource(private val context: Context) : OpticsSource {

    override suspend fun fieldOfView(): CameraFieldOfView {
        val manager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager

        return runCatching {
            val cameraId = manager.cameraIdList.firstOrNull { id ->
                manager.getCameraCharacteristics(id)
                    .get(CameraCharacteristics.LENS_FACING) == CameraCharacteristics.LENS_FACING_BACK
            } ?: manager.cameraIdList.firstOrNull() ?: return CameraFieldOfView.Default

            val characteristics = manager.getCameraCharacteristics(cameraId)
            val focal = characteristics
                .get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS)
                ?.firstOrNull()
            val sensor = characteristics.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE)

            if (focal == null || sensor == null) {
                CameraFieldOfView.Default
            } else {
                // Экран AR заблокирован в портретной ориентации.
                fieldOfViewFrom(focal, sensor.width, sensor.height, portrait = true)
            }
        }.getOrElse { error ->
            Log.w(TAG, "Не удалось прочитать характеристики камеры, берём значение по умолчанию", error)
            CameraFieldOfView.Default
        }
    }

    private companion object {
        const val TAG = "CameraOpticsSource"
    }
}
