package ru.marshruty.client;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import ru.marshruty.client.nfc.NfcPlugin;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Плагины подключаются до super.onCreate: мост собирает их при старте.
        registerPlugin(NfcPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
