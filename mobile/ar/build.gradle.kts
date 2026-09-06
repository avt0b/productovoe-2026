plugins {
    // AGP 9 несёт поддержку Kotlin внутри себя — отдельный kotlin-android
    // подключать нельзя, он конфликтует за расширение `kotlin`.
    alias(libs.plugins.android.library)
}

android {
    namespace = "ru.marshruty.ar"
    compileSdk = 37

    defaultConfig {
        minSdk = 26
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    testImplementation(libs.junit)
}
