plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.kotlin.compose) apply false
    // Только на classpath: поднимает KGP для встроенного в AGP Kotlin до 2.4.10.
    alias(libs.plugins.kotlin.android) apply false
}
