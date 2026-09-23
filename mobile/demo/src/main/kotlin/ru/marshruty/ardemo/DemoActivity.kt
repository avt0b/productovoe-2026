package ru.marshruty.ardemo

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import ru.marshruty.ar.ArPointContract
import ru.marshruty.ar.ArResult
import ru.marshruty.ar.ArTarget
import ru.marshruty.ar.domain.GeoPoint
import ru.marshruty.ar.sim.Simulation

/**
 * Стенд для полевой проверки AR-модуля.
 *
 * Смысл экрана — не красота, а возможность за минуту проверить наведение на
 * настоящей местности: взять свои координаты, отойти на два десятка шагов,
 * подставить их целью и посмотреть, встанет ли метка туда, куда надо.
 */
class DemoActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) { DemoScreen() }
            }
        }
    }
}

@Composable
private fun DemoScreen() {
    val context = LocalContext.current

    var latitude by remember { mutableStateOf(Simulation.Target.latitude.toString()) }
    var longitude by remember { mutableStateOf(Simulation.Target.longitude.toString()) }
    var label by remember { mutableStateOf("След кабельного окопа") }
    var audioUri by remember { mutableStateOf("") }
    var lastResult by remember { mutableStateOf<String?>(null) }
    var hint by remember { mutableStateOf<String?>(null) }

    val launcher = rememberLauncherForActivityResult(ArPointContract()) { result ->
        lastResult = when (result) {
            is ArResult.Completed -> "Точка засчитана: ${result.pointId}"
            is ArResult.Dismissed -> "Выход без прохождения: ${result.pointId}"
            is ArResult.Unavailable -> "Недоступно: ${result.reason}"
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions(),
    ) { }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Стенд AR-модуля", style = MaterialTheme.typography.headlineSmall)
        Text(
            "Порядок проверки: снять свои координаты, отойти на 20–40 шагов, " +
                "вписать снятые координаты целью и открыть AR. Метка должна " +
                "оказаться там, откуда вы пришли.",
            style = MaterialTheme.typography.bodyMedium,
        )

        OutlinedButton(
            onClick = {
                permissionLauncher.launch(
                    arrayOf(Manifest.permission.CAMERA, Manifest.permission.ACCESS_FINE_LOCATION),
                )
            },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Запросить разрешения") }

        OutlinedButton(
            onClick = {
                val point = readLastKnownPoint(context)
                if (point == null) {
                    hint = "Позиция не получена: включите геолокацию и выйдите на открытое место"
                } else {
                    latitude = "%.6f".format(point.latitude)
                    longitude = "%.6f".format(point.longitude)
                    hint = "Координаты подставлены. Отойдите и открывайте AR."
                }
            },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Взять мои текущие координаты") }

        OutlinedTextField(
            value = latitude,
            onValueChange = { latitude = it },
            label = { Text("Широта цели") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = longitude,
            onValueChange = { longitude = it },
            label = { Text("Долгота цели") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = label,
            onValueChange = { label = it },
            label = { Text("Подпись метки") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        // Записанного голоса у сценария нет — он приходит с бэкенда под точку.
        // Здесь ссылку подставляют руками: иначе синхронность голоса и субтитров
        // проверить нечем.
        OutlinedTextField(
            value = audioUri,
            onValueChange = { audioUri = it },
            label = { Text("Озвучка: ссылка или путь в assets") },
            placeholder = { Text("пусто — рассказ пойдёт субтитрами") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        // Одна точка, два режима: с маркером проводник встаёт на картинку через
        // ARCore, без маркера — прежний экран на CameraX и компасе.
        fun launchPoint(withMarker: Boolean) {
            val lat = latitude.trim().toDoubleOrNull()
            val lon = longitude.trim().toDoubleOrNull()
            if (lat == null || lon == null) {
                hint = "Координаты не разобраны — нужны числа, разделитель точка"
                return
            }
            hint = null
            launcher.launch(
                Simulation.point.copy(
                    target = ArTarget(GeoPoint(lat, lon), label = label),
                    marker = Simulation.marker.takeIf { withMarker },
                    narration = Simulation.point.narration.copy(
                        audioUri = audioUri.trim().ifEmpty { null },
                    ),
                ),
            )
        }

        Button(
            onClick = { launchPoint(withMarker = true) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Открыть AR с маркером") }

        OutlinedButton(
            onClick = { launchPoint(withMarker = false) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Открыть AR без маркера (компас)") }

        OutlinedButton(
            onClick = { launcher.launch(Simulation.memorialPoint) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Открыть точку без проводника (мемориал)") }

        hint?.let { Text(it, style = MaterialTheme.typography.bodySmall) }

        lastResult?.let { result ->
            Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text("Результат", style = MaterialTheme.typography.labelLarge)
                    Text(result, fontFamily = FontFamily.Monospace)
                }
            }
        }
    }
}

/**
 * Последняя известная позиция — только для стенда.
 * В самом модуле подписка живая, здесь достаточно одного снимка.
 */
@SuppressLint("MissingPermission")
private fun readLastKnownPoint(context: Context): GeoPoint? {
    val granted = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) ==
        PackageManager.PERMISSION_GRANTED
    if (!granted) return null

    val manager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    return listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
        .asSequence()
        .mapNotNull { provider -> runCatching { manager.getLastKnownLocation(provider) }.getOrNull() }
        .firstOrNull()
        ?.let { GeoPoint(it.latitude, it.longitude) }
}
