plugins {
    // AGP 9 несёт поддержку Kotlin внутри себя — отдельный kotlin-android
    // подключать нельзя, он конфликтует за расширение `kotlin`.
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.compose)
    // APK клиента (frontend/client) подключает модуль готовым AAR из локального
    // репозитория: там Capacitor на AGP 8, а AGP двух версий в одной сборке
    // Gradle не пускает.
    `maven-publish`
}

android {
    namespace = "ru.marshruty.ar"
    compileSdk = 37

    defaultConfig {
        minSdk = 26
        // Собираемся против 37 (другой платформы в SDK нет), но API 37 не зовём.
        // APK клиента на Capacitor собирается против 36 — без этого AGP его не пустит.
        aarMetadata {
            minCompileSdk = 36
        }
    }

    buildFeatures {
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    publishing {
        singleVariant("release")
    }
}

// gradlew :ar:publishReleasePublicationToLocalRepository → ar/build/repo.
// Оттуда его берёт APK клиента: frontend/client, `npm run android:ar`.
publishing {
    publications {
        register<MavenPublication>("release") {
            groupId = "ru.marshruty"
            artifactId = "ar"
            version = "0.1.0"
            afterEvaluate { from(components["release"]) }
        }
    }
    repositories {
        maven {
            name = "local"
            url = uri(layout.buildDirectory.dir("repo"))
        }
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)

    val composeBom = platform(libs.compose.bom)
    implementation(composeBom)
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.material3)
    implementation(libs.compose.foundation)
    implementation(libs.compose.animation)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.kotlinx.coroutines.android)

    implementation(libs.arsceneview)

    // Чтение QR с кадра ARCore: запасной способ вызвать проводника, когда
    // картинку-табличку поймать не удаётся. Чистая Java, без Play Services —
    // модуль остаётся работоспособным на телефонах без сервисов Google.
    implementation(libs.zxing.core)

    implementation(libs.camera.core)
    implementation(libs.camera.camera2)
    implementation(libs.camera.lifecycle)
    implementation(libs.camera.view)
    // Превью — часть модуля: экран должен открываться в студии без телефона.
    implementation(libs.compose.ui.tooling.preview)
    debugImplementation(libs.compose.ui.tooling)

    testImplementation(libs.junit)
}
