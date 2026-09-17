package ru.marshruty.ar.data

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Looper
import androidx.core.content.ContextCompat
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.conflate
import ru.marshruty.ar.domain.GeoPoint
import ru.marshruty.ar.domain.LocationFix

/**
 * Геопозиция через системный `LocationManager`.
 *
 * Намеренно без Google Play Services: `FusedLocationProviderClient` точнее в
 * городе, но тянет зависимость от сервисов Google, которых на части устройств
 * просто нет. Поисковики работают в поле, где всё равно решает GPS, а не
 * триангуляция по вышкам.
 */
class PlatformLocationSource(private val context: Context) : LocationSource {

    private val locationManager =
        context.getSystemService(Context.LOCATION_SERVICE) as LocationManager

    /** Последняя известная позиция — нужна для расчёта магнитного склонения. */
    @Volatile
    var lastPoint: GeoPoint? = null
        private set

    val hasPermission: Boolean
        get() = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) ==
            PackageManager.PERMISSION_GRANTED

    @SuppressLint("MissingPermission") // проверяется в hasPermission перед подпиской
    override val fix: Flow<LocationFix?> = callbackFlow {
        if (!hasPermission) {
            trySend(null)
            close()
            return@callbackFlow
        }

        val listener = LocationListener { location -> trySend(location.toFix()) }

        // Сеть даёт грубую позицию сразу, GPS — точную, но не мгновенно.
        // Подписываемся на оба: первый экран не должен ждать спутников.
        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
            .filter { runCatching { locationManager.isProviderEnabled(it) }.getOrDefault(false) }

        if (providers.isEmpty()) {
            trySend(null)
        } else {
            providers.forEach { provider ->
                locationManager.getLastKnownLocation(provider)?.let { trySend(it.toFix()) }
                locationManager.requestLocationUpdates(
                    provider,
                    UPDATE_INTERVAL_MS,
                    UPDATE_DISTANCE_M,
                    listener,
                    Looper.getMainLooper(),
                )
            }
        }

        awaitClose { locationManager.removeUpdates(listener) }
    }.conflate()

    private fun Location.toFix(): LocationFix {
        val point = GeoPoint(latitude, longitude)
        lastPoint = point
        return LocationFix(
            point = point,
            // Без заявленной точности считаем позицию заведомо негодной:
            // лучше спрятать метку, чем показать её не там.
            accuracyMeters = if (hasAccuracy()) accuracy.toDouble() else UNKNOWN_ACCURACY_M,
        )
    }

    private companion object {
        const val UPDATE_INTERVAL_MS = 1_000L
        const val UPDATE_DISTANCE_M = 1f
        const val UNKNOWN_ACCURACY_M = 999.0
    }
}
