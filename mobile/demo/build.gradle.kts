plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "ru.marshruty.ardemo"
    compileSdk = 37

    defaultConfig {
        applicationId = "ru.marshruty.ardemo"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1"

        // Filament везёт нативные библиотеки под четыре ABI и раздувает APK
        // до ~40 МБ. Оставляем реальный телефон и эмулятор.
        ndk { abiFilters += listOf("arm64-v8a", "x86_64") }
    }

    buildFeatures {
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
        }
    }
}

dependencies {
    implementation(project(":ar"))

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)

    val composeBom = platform(libs.compose.bom)
    implementation(composeBom)
    implementation(libs.compose.ui)
    implementation(libs.compose.material3)
    implementation(libs.compose.foundation)
    debugImplementation(libs.compose.ui.tooling)
}
