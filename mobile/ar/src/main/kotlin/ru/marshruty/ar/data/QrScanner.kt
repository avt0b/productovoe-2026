package ru.marshruty.ar.data

import android.media.Image
import com.google.zxing.BinaryBitmap
import com.google.zxing.DecodeHintType
import com.google.zxing.PlanarYUVLuminanceSource
import com.google.zxing.common.HybridBinarizer
import com.google.zxing.qrcode.QRCodeReader

/**
 * Чтение QR с кадра ARCore.
 *
 * Кадр приходит в YUV, и для распознавания нужна только яркость — плоскость Y
 * лежит первой и читается как есть, без перевода в RGB и без копии картинки
 * целиком. Это важнее, чем кажется: декодер зовётся прямо в кадровом колбэке
 * сессии, и лишние миллисекунды там видны как рывки картинки.
 */
internal class QrScanner {

    private val reader = QRCodeReader()

    private val hints = mapOf(
        // Код в кадре мелкий, под углом и с бликами от экрана: пусть декодер
        // старается. Кадры всё равно сканируются не каждый, а по таймеру.
        DecodeHintType.TRY_HARDER to true,
    )

    /** Содержимое кода или `null`, если кода в кадре нет. */
    fun read(image: Image): String? {
        val plane = image.planes.firstOrNull() ?: return null
        val buffer = plane.buffer
        val data = ByteArray(buffer.remaining())
        buffer.get(data)

        // Шаг строки бывает больше ширины кадра — у ARCore это обычное дело.
        // PlanarYUVLuminanceSource ждёт плотные строки, поэтому лишние байты
        // в конце каждой строки выбрасываем.
        val rowStride = plane.rowStride
        val width = image.width
        val height = image.height
        val luminance = if (rowStride == width) {
            data
        } else {
            ByteArray(width * height).also { packed ->
                for (row in 0 until height) {
                    val from = row * rowStride
                    if (from + width > data.size) break
                    System.arraycopy(data, from, packed, row * width, width)
                }
            }
        }

        val source = PlanarYUVLuminanceSource(luminance, width, height, 0, 0, width, height, false)
        return decode(BinaryBitmap(HybridBinarizer(source)))
            // Половина кадров приходит перевёрнутой по яркости — тёмный код на
            // светлом экране телефона читается именно так.
            ?: decode(BinaryBitmap(HybridBinarizer(source.invert())))
    }

    private fun decode(bitmap: BinaryBitmap): String? = try {
        reader.decode(bitmap, hints).text
    } catch (_: Exception) {
        // NotFoundException в кадре без кода — норма, а не ошибка: он прилетает
        // десятки раз за сеанс. Ошибки формата и контрольной суммы значат то же
        // самое — «читать нечего».
        null
    } finally {
        reader.reset()
    }
}
