package ru.marshruty.client.nfc;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.nfc.FormatException;
import android.nfc.NdefMessage;
import android.nfc.NdefRecord;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
import android.nfc.tech.NdefFormatable;
import android.os.Parcelable;
import android.provider.Settings;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

/**
 * Чтение и запись NFC-меток.
 *
 * Пока приложение открыто, метки ловит режим чтения (`enableReaderMode`): он
 * работает, только когда экран активен, и не даёт системе перехватывать метку
 * своим окном. Метку с нашей ссылкой (`marshruty://…`) система отдаёт
 * приложению и когда оно закрыто — такое открытие разбирается в
 * {@link #load()} и {@link #handleOnNewIntent(Intent)}: ссылка уходит событием
 * `nfcLink` и открывает свой экран, сама метка ждёт экран NFC.
 *
 * Разрешений у пользователя не спрашиваем: NFC выдаётся при установке.
 */
@CapacitorPlugin(name = "MarshrutyNfc")
public class NfcPlugin extends Plugin implements NfcAdapter.ReaderCallback {

    /** Типы меток, которые слушаем: обычные наклейки, карты, брелоки. */
    private static final int READER_FLAGS =
        NfcAdapter.FLAG_READER_NFC_A |
        NfcAdapter.FLAG_READER_NFC_B |
        NfcAdapter.FLAG_READER_NFC_F |
        NfcAdapter.FLAG_READER_NFC_V;

    /** Префиксы URI из стандарта NDEF: в метке хранится номер префикса, а не весь адрес. */
    private static final String[] URI_PREFIXES = {
        "", "http://www.", "https://www.", "http://", "https://", "tel:", "mailto:",
        "ftp://anonymous:anonymous@", "ftp://ftp.", "ftps://", "sftp://", "smb://",
        "nfs://", "ftp://", "dav://", "news:", "telnet://", "imap:", "rtsp://", "urn:",
        "pop:", "sip:", "sips:", "tftp:", "btspp://", "btl2cap://", "btgoep://",
        "tcpobex://", "irdaobex://", "file://", "urn:epc:id:", "urn:epc:tag:",
        "urn:epc:pat:", "urn:epc:raw:", "urn:epc:", "urn:nfc:",
    };

    private NfcAdapter adapter;
    private boolean scanning;
    /** Метка, которой открыли приложение: её заберёт экран, когда откроется. */
    private JSObject launchTag;
    /** Запись ждёт, пока человек приложит метку. */
    private PluginCall pendingWrite;
    private NdefMessage pendingMessage;

    @Override
    public void load() {
        adapter = NfcAdapter.getDefaultAdapter(getContext());
        Activity activity = getActivity();
        if (activity != null) {
            launchTag = fromIntent(activity.getIntent());
        }
    }

    @PluginMethod
    public void status(PluginCall call) {
        JSObject answer = new JSObject();
        answer.put("supported", adapter != null);
        answer.put("enabled", adapter != null && adapter.isEnabled());
        call.resolve(answer);
    }

    @PluginMethod
    public void startScan(PluginCall call) {
        if (adapter == null) {
            call.reject("На этом устройстве нет NFC", "unsupported");
            return;
        }
        if (!adapter.isEnabled()) {
            call.reject("NFC выключен — включите его в настройках телефона", "disabled");
            return;
        }
        scanning = true;
        enableReader();
        call.resolve();
    }

    @PluginMethod
    public void stopScan(PluginCall call) {
        scanning = false;
        disableReader();
        call.resolve();
    }

    /** Записать на следующую приложенную метку. Ответ придёт, когда метку приложат. */
    @PluginMethod
    public void write(PluginCall call) {
        if (adapter == null || !adapter.isEnabled()) {
            call.reject("NFC недоступен", "disabled");
            return;
        }
        NdefRecord record;
        String uri = call.getString("uri");
        String text = call.getString("text");
        if (uri != null && !uri.isEmpty()) {
            record = NdefRecord.createUri(uri);
        } else if (text != null && !text.isEmpty()) {
            record = NdefRecord.createTextRecord("ru", text);
        } else {
            call.reject("Нечего записывать: нужен text или uri");
            return;
        }

        cancelPendingWrite("Запись отменена — начали новую");
        pendingMessage = new NdefMessage(new NdefRecord[] { record });
        call.setKeepAlive(true);
        pendingWrite = call;

        scanning = true;
        enableReader();
    }

    /** Отменить ожидание записи. */
    @PluginMethod
    public void cancelWrite(PluginCall call) {
        cancelPendingWrite("Запись отменена");
        call.resolve();
    }

    /** Метка, которой открыли приложение. Отдаётся один раз. */
    @PluginMethod
    public void consumeLaunchTag(PluginCall call) {
        JSObject answer = new JSObject();
        answer.put("tag", launchTag);
        launchTag = null;
        call.resolve(answer);
    }

    /** Открыть настройки NFC — когда он выключен. */
    @PluginMethod
    public void openSettings(PluginCall call) {
        getContext().startActivity(new Intent(Settings.ACTION_NFC_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
        call.resolve();
    }

    @Override
    public void onTagDiscovered(Tag tag) {
        if (pendingWrite != null && pendingMessage != null) {
            writeTo(tag);
            return;
        }
        notifyListeners("nfcTag", describe(tag));
    }

    /**
     * Сюда приходит и запуск приложения меткой: мост вызывает этот метод и для
     * интента, с которым приложение стартовало.
     */
    @Override
    protected void handleOnNewIntent(Intent intent) {
        super.handleOnNewIntent(intent);
        announceLink(intent);
        JSObject tag = fromIntent(intent);
        if (tag == null) {
            return;
        }
        // Экран уже открыт — отдаём метку ему; иначе она подождёт в launchTag.
        if (hasListeners("nfcTag")) {
            notifyListeners("nfcTag", tag);
        } else {
            launchTag = tag;
        }
    }

    // Режим чтения живёт, только пока экран активен.
    @Override
    protected void handleOnResume() {
        if (scanning) {
            enableReader();
        }
    }

    @Override
    protected void handleOnPause() {
        disableReader();
    }

    @Override
    protected void handleOnDestroy() {
        cancelPendingWrite("Экран закрыт");
        disableReader();
    }

    private void enableReader() {
        Activity activity = getActivity();
        if (adapter == null || activity == null) {
            return;
        }
        activity.runOnUiThread(() -> adapter.enableReaderMode(activity, this, READER_FLAGS, null));
    }

    private void disableReader() {
        Activity activity = getActivity();
        if (adapter == null || activity == null) {
            return;
        }
        activity.runOnUiThread(() -> adapter.disableReaderMode(activity));
    }

    private void cancelPendingWrite(String reason) {
        if (pendingWrite != null) {
            pendingWrite.reject(reason, "cancelled");
        }
        pendingWrite = null;
        pendingMessage = null;
    }

    private void writeTo(Tag tag) {
        PluginCall call = pendingWrite;
        NdefMessage message = pendingMessage;
        pendingWrite = null;
        pendingMessage = null;
        if (call == null || message == null) {
            return;
        }

        Ndef ndef = Ndef.get(tag);
        try {
            if (ndef != null) {
                ndef.connect();
                if (!ndef.isWritable()) {
                    call.reject("Метка защищена от записи", "read-only");
                    return;
                }
                if (ndef.getMaxSize() < message.toByteArray().length) {
                    call.reject("Не помещается: на метке " + ndef.getMaxSize() + " байт", "too-big");
                    return;
                }
                ndef.writeNdefMessage(message);
            } else {
                NdefFormatable blank = NdefFormatable.get(tag);
                if (blank == null) {
                    call.reject("Эта метка не умеет хранить данные", "not-ndef");
                    return;
                }
                blank.connect();
                blank.format(message);
                blank.close();
            }
            JSObject answer = new JSObject();
            answer.put("tag", describe(tag));
            call.resolve(answer);
        } catch (IOException | FormatException | SecurityException error) {
            call.reject("Не удалось записать: " + error.getMessage(), "write-failed");
        } finally {
            if (ndef != null) {
                try {
                    ndef.close();
                } catch (IOException | SecurityException ignored) {
                    // Метку уже унесли — для записи это ничего не меняет.
                }
            }
        }
    }

    /**
     * Ссылка с нашей метки должна открыть свой экран. Системный запуск меткой
     * приходит как NDEF_DISCOVERED, а плагин App из Capacitor передаёт в
     * `appUrlOpen` только VIEW, поэтому без этого события приложение
     * открывалось на главной. Событие ждёт, пока приложение подпишется:
     * при запуске с метки оно приходит раньше, чем загрузится страница.
     */
    private void announceLink(Intent intent) {
        if (intent == null || !NfcAdapter.ACTION_NDEF_DISCOVERED.equals(intent.getAction())) {
            return;
        }
        Uri data = intent.getData();
        if (data == null || !"marshruty".equals(data.getScheme())) {
            return;
        }
        JSObject link = new JSObject();
        link.put("url", data.toString());
        notifyListeners("nfcLink", link, true);
    }

    /**
     * Метка из системного открытия приложения (NDEF_DISCOVERED).
     *
     * Записи берём из интента: система уже прочла их, пока выбирала
     * приложение. Читать метку заново нельзя — к этому моменту её обычно
     * убрали, и Android отвечает SecurityException «Tag is out of date»:
     * при запуске меткой из-за этого не загружался плагин, при открытом
     * приложении — падало всё приложение.
     */
    private JSObject fromIntent(Intent intent) {
        if (intent == null || !NfcAdapter.ACTION_NDEF_DISCOVERED.equals(intent.getAction())) {
            return null;
        }
        Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
        if (tag == null) {
            return null;
        }
        Parcelable[] messages = intent.getParcelableArrayExtra(NfcAdapter.EXTRA_NDEF_MESSAGES);
        if (messages == null) {
            return describe(tag);
        }
        JSObject out = header(tag);
        JSArray records = new JSArray();
        for (Parcelable message : messages) {
            if (message instanceof NdefMessage) {
                for (NdefRecord record : ((NdefMessage) message).getRecords()) {
                    records.put(describe(record));
                }
            }
        }
        out.put("records", records);
        return out;
    }

    /** Что на метке: идентификатор, технологии, записи NDEF, можно ли писать. */
    private JSObject describe(Tag tag) {
        JSObject out = header(tag);
        JSArray records = new JSArray();
        Ndef ndef = Ndef.get(tag);
        if (ndef != null) {
            try {
                ndef.connect();
                NdefMessage message = ndef.getNdefMessage();
                if (message != null) {
                    for (NdefRecord record : message.getRecords()) {
                        records.put(describe(record));
                    }
                }
            } catch (IOException | FormatException | SecurityException error) {
                // SecurityException — метку уже убрали и система её «забыла».
                out.put("error", "Метку убрали слишком быстро — приложите ещё раз");
            } finally {
                try {
                    ndef.close();
                } catch (IOException | SecurityException ignored) {
                    // Читать уже нечего.
                }
            }
        }
        out.put("records", records);
        return out;
    }

    /** Идентификатор, технологии и можно ли писать — без обращения к самой метке. */
    private JSObject header(Tag tag) {
        JSObject out = new JSObject();
        out.put("id", hex(tag.getId()));

        JSArray techs = new JSArray();
        for (String tech : tag.getTechList()) {
            techs.put(tech.substring(tech.lastIndexOf('.') + 1));
        }
        out.put("techs", techs);

        Ndef ndef = Ndef.get(tag);
        if (ndef == null) {
            out.put("writable", NdefFormatable.get(tag) != null);
            out.put("maxSize", null);
        } else {
            out.put("writable", ndef.isWritable());
            out.put("maxSize", ndef.getMaxSize());
        }
        return out;
    }

    private JSObject describe(NdefRecord record) {
        JSObject out = new JSObject();
        byte[] payload = record.getPayload();

        if (record.getTnf() == NdefRecord.TNF_WELL_KNOWN && java.util.Arrays.equals(record.getType(), NdefRecord.RTD_TEXT)) {
            out.put("kind", "text");
            out.put("text", text(payload));
            return out;
        }
        if (record.getTnf() == NdefRecord.TNF_WELL_KNOWN && java.util.Arrays.equals(record.getType(), NdefRecord.RTD_URI)) {
            out.put("kind", "uri");
            out.put("uri", uri(payload));
            return out;
        }
        if (record.getTnf() == NdefRecord.TNF_MIME_MEDIA) {
            out.put("kind", "mime");
            out.put("mime", new String(record.getType(), StandardCharsets.US_ASCII));
            out.put("text", new String(payload, StandardCharsets.UTF_8));
            return out;
        }
        out.put("kind", "unknown");
        out.put("text", hex(payload));
        return out;
    }

    /** Текстовая запись: первый байт — кодировка и длина кода языка, дальше сам текст. */
    private String text(byte[] payload) {
        if (payload.length == 0) {
            return "";
        }
        int languageLength = payload[0] & 0x3F;
        boolean utf16 = (payload[0] & 0x80) != 0;
        int from = 1 + languageLength;
        if (from > payload.length) {
            return "";
        }
        return new String(payload, from, payload.length - from, utf16 ? StandardCharsets.UTF_16 : StandardCharsets.UTF_8);
    }

    /** Адресная запись: первый байт — номер префикса из стандарта. */
    private String uri(byte[] payload) {
        if (payload.length == 0) {
            return "";
        }
        int prefix = payload[0] & 0xFF;
        String head = prefix < URI_PREFIXES.length ? URI_PREFIXES[prefix] : "";
        return head + new String(payload, 1, payload.length - 1, StandardCharsets.UTF_8);
    }

    private String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte value : bytes) {
            out.append(String.format("%02X", value));
        }
        return out.toString();
    }
}
