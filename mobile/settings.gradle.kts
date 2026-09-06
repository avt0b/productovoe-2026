pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode = RepositoriesMode.FAIL_ON_PROJECT_REPOS
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "marshruty-mobile"

// :ar — самостоятельный AR-модуль. Хост-приложение подключит его как зависимость,
// поэтому модуль не знает ничего о том, кто его запускает.
include(":ar")
