package ru.marshruty.ar.ui

import android.util.Log
import androidx.camera.core.CameraSelector
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner

/**
 * Живой кадр задней камеры.
 *
 * Только `Preview` — ни анализа кадров, ни съёмки: экрану нужен фон, а не
 * обработка изображения. Отсюда и низкое энергопотребление, и мгновенный старт.
 *
 * `FILL_CENTER` растягивает кадр на весь экран и обрезает лишнее — выглядит
 * правильно, но реальный угол обзора становится меньше паспортного. Поправку
 * считает `croppedFieldOfView`, иначе метка уезжает от цели.
 */
@Composable
fun CameraPreview(
    modifier: Modifier = Modifier,
    onFailure: (Throwable) -> Unit = {},
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val previewView = remember {
        PreviewView(context).apply {
            // COMPATIBLE (TextureView) вместо PERFORMANCE: на части устройств
            // SurfaceView не уживается с composable-слоями поверх него.
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
            scaleType = PreviewView.ScaleType.FILL_CENTER
        }
    }

    DisposableEffect(lifecycleOwner) {
        val future = ProcessCameraProvider.getInstance(context)
        var provider: ProcessCameraProvider? = null

        future.addListener({
            runCatching {
                provider = future.get()
                val preview = Preview.Builder().build().apply {
                    surfaceProvider = previewView.surfaceProvider
                }
                provider?.unbindAll()
                provider?.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview)
            }.onFailure { error ->
                Log.e(TAG, "Не удалось запустить камеру", error)
                onFailure(error)
            }
        }, ContextCompat.getMainExecutor(context))

        onDispose { provider?.unbindAll() }
    }

    AndroidView(factory = { previewView }, modifier = modifier)
}

private const val TAG = "ArCameraPreview"
