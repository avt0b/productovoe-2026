package ru.marshruty.ar.ui

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp

/**
 * Токены перенесены из макета Google Stitch один в один.
 * Новый цвет или размер добавляется сюда, а не в композабл.
 */
object ArColors {
    val Primary = Color(0xFF324523)
    val PrimaryContainer = Color(0xFF495D38)
    val PrimaryFixed = Color(0xFFD2EABA)
    val OnPrimary = Color(0xFFFFFFFF)

    val Secondary = Color(0xFF51643A)

    val Tertiary = Color(0xFF673100)
    val TertiaryContainer = Color(0xFF8B4300)
    val OnTertiary = Color(0xFFFFFFFF)
    val TertiaryFixed = Color(0xFFFFDCC6)
    val TertiaryFixedDim = Color(0xFFFFB786)
    val OnTertiaryFixed = Color(0xFF311300)
    val OnTertiaryContainer = Color(0xFFFFC096)

    val InverseSurface = Color(0xFF31312B)
    val InverseOnSurface = Color(0xFFF3F1E8)
    val SurfaceBright = Color(0xFFFCF9F1)
    val SurfaceContainerHighest = Color(0xFFE5E2DA)

    val Outline = Color(0xFF75786E)
    val Error = Color(0xFFBA1A1A)
    val ErrorContainer = Color(0xFFFFDAD6)
}

/**
 * Шрифтовые роли макета. Настоящие гарнитуры (Oswald, Work Sans, Noto Serif,
 * Space Mono) сюда подключаются файлами в `res/font` — пока взяты системные
 * семейства с теми же начертаниями и метриками, чтобы не тащить ассеты
 * раньше времени. Размеры, межбуквенные интервалы и веса — из макета.
 */
object ArType {
    val HeadlineSm = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontSize = 18.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.04.em,
        fontWeight = FontWeight.SemiBold,
    )

    val LabelArchiveCode = TextStyle(
        fontFamily = FontFamily.Monospace,
        fontSize = 11.sp,
        lineHeight = 14.sp,
        letterSpacing = 0.08.em,
        fontWeight = FontWeight.Normal,
    )

    val LabelCoordinate = TextStyle(
        fontFamily = FontFamily.Monospace,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.05.em,
        fontWeight = FontWeight.Bold,
    )

    val LabelAction = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontSize = 13.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.03.em,
        fontWeight = FontWeight.SemiBold,
    )

    val BodyMd = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontSize = 14.sp,
        lineHeight = 20.sp,
    )

    val BodySm = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontSize = 12.sp,
        lineHeight = 16.sp,
    )

    /** Прямая речь проводника — засечный шрифт, как в мемориальном режиме макета. */
    val MemorialQuote = TextStyle(
        fontFamily = FontFamily.Serif,
        fontSize = 18.sp,
        lineHeight = 28.sp,
    )
}
