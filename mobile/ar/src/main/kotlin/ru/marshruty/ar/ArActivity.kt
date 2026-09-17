package ru.marshruty.ar

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContract
import ru.marshruty.ar.ui.ArHost

/**
 * Экран AR как отдельная Activity.
 *
 * Хост запускает его через [ArPointContract] и получает [ArResult] — ему не
 * нужно знать ни про камеру, ни про датчики, ни про разрешения. Ориентация
 * зафиксирована портретной в манифесте: пересчёт осей датчика для альбомной
 * был бы другим.
 */
class ArActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        // Пока человек водит камерой в поисках метки, он не трогает экран —
        // без этого флага телефон гаснет на середине поиска.
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val spec = intent.readSpec()
        if (spec == null) {
            finish()
            return
        }

        // Умолчание: любой выход, кроме явного успеха, — отказ.
        setResult(Activity.RESULT_OK, ArResult.Dismissed(spec.pointId).toIntent())

        setContent {
            ArHost(
                spec = spec,
                onFinish = { result ->
                    setResult(Activity.RESULT_OK, result.toIntent())
                    finish()
                },
            )
        }
    }

    private fun Intent.readSpec(): ArPointSpec? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            getSerializableExtra(EXTRA_SPEC, ArPointSpec::class.java)
        } else {
            @Suppress("DEPRECATION")
            getSerializableExtra(EXTRA_SPEC) as? ArPointSpec
        }

    companion object {
        internal const val EXTRA_SPEC = "ru.marshruty.ar.SPEC"
        internal const val EXTRA_POINT_ID = "ru.marshruty.ar.POINT_ID"
        internal const val EXTRA_OUTCOME = "ru.marshruty.ar.OUTCOME"
        internal const val EXTRA_REASON = "ru.marshruty.ar.REASON"
    }
}

private fun ArResult.toIntent(): Intent = Intent().apply {
    when (this@toIntent) {
        is ArResult.Completed -> {
            putExtra(ArActivity.EXTRA_OUTCOME, "completed")
            putExtra(ArActivity.EXTRA_POINT_ID, pointId)
        }
        is ArResult.Dismissed -> {
            putExtra(ArActivity.EXTRA_OUTCOME, "dismissed")
            putExtra(ArActivity.EXTRA_POINT_ID, pointId)
        }
        is ArResult.Unavailable -> {
            putExtra(ArActivity.EXTRA_OUTCOME, "unavailable")
            putExtra(ArActivity.EXTRA_POINT_ID, pointId)
            putExtra(ArActivity.EXTRA_REASON, reason.name)
        }
    }
}

/**
 * Контракт запуска для хоста.
 *
 * ```kotlin
 * val launcher = registerForActivityResult(ArPointContract()) { result -> … }
 * launcher.launch(pointSpec)
 * ```
 */
class ArPointContract : ActivityResultContract<ArPointSpec, ArResult>() {

    override fun createIntent(context: Context, input: ArPointSpec): Intent =
        Intent(context, ArActivity::class.java).putExtra(ArActivity.EXTRA_SPEC, input)

    override fun parseResult(resultCode: Int, intent: Intent?): ArResult {
        val pointId = intent?.getStringExtra(ArActivity.EXTRA_POINT_ID).orEmpty()
        return when (intent?.getStringExtra(ArActivity.EXTRA_OUTCOME)) {
            "completed" -> ArResult.Completed(pointId)
            "unavailable" -> ArResult.Unavailable(
                pointId = pointId,
                reason = runCatching {
                    ArResult.Unavailable.Reason.valueOf(
                        intent.getStringExtra(ArActivity.EXTRA_REASON).orEmpty(),
                    )
                }.getOrDefault(ArResult.Unavailable.Reason.NO_CAMERA),
            )
            // Система могла убить экран сама — это тоже отказ, а не прохождение.
            else -> ArResult.Dismissed(pointId)
        }
    }
}
