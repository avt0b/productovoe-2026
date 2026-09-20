package ru.marshruty.client;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.Plugin;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerArPlugin();
        super.onCreate(savedInstanceState);
    }

    /**
     * Мост в AR-модуль подключается, только если APK собран вместе с ним
     * (`npm run android:ar`). Без него приложение работает как обычно, а кнопка
     * «Запустить AR-поиск» честно говорит, что AR в этой сборке нет.
     */
    @SuppressWarnings("unchecked")
    private void registerArPlugin() {
        try {
            Class<?> plugin = Class.forName("ru.marshruty.client.ar.ArPlugin");
            registerPlugin((Class<? extends Plugin>) plugin);
        } catch (ClassNotFoundException absent) {
            // Сборка без AR — это нормально, а не ошибка.
        }
    }
}
