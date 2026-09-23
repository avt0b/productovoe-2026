package ru.marshruty.client.ar;

import android.content.Intent;
import android.content.res.AssetManager;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import ru.marshruty.ar.ArPointContract;
import ru.marshruty.ar.ArPointSpec;
import ru.marshruty.ar.ArResult;
import ru.marshruty.ar.ArTarget;
import ru.marshruty.ar.CompanionSpec;
import ru.marshruty.ar.MarkerSpec;
import ru.marshruty.ar.NarrationSpec;
import ru.marshruty.ar.SubtitleLine;
import ru.marshruty.ar.domain.GeoPoint;

/**
 * Мост между приложением на Vue и AR-модулем из `mobile/ar`.
 *
 * Модуль ничего не знает о приложении: ему отдают точку ({@link ArPointSpec}),
 * он возвращает результат. Здесь — только перевод JSON в контракт модуля и
 * обратно; вся AR-логика живёт в `mobile/ar` и правится там.
 *
 * Файл лежит в отдельном source set `src/ar/java`: нет собранного AAR — нет и
 * моста, APK собирается без AR.
 */
@CapacitorPlugin(name = "MarshrutyAr")
public class ArPlugin extends Plugin {

    /** Папка с моделями проводника в assets AAR. */
    private static final String COMPANION_DIR = "companion";

    @PluginMethod
    public void open(PluginCall call) {
        ArPointSpec spec;
        try {
            spec = buildSpec(call);
        } catch (JSONException | IllegalArgumentException error) {
            call.reject("Точку для AR собрать не удалось: " + error.getMessage());
            return;
        }
        startActivityForResult(call, new ArPointContract().createIntent(getContext(), spec), "onArResult");
    }

    @ActivityCallback
    private void onArResult(PluginCall call, ActivityResult activityResult) {
        if (call == null) {
            return;
        }
        ArResult result = new ArPointContract().parseResult(activityResult.getResultCode(), activityResult.getData());
        JSObject answer = new JSObject();
        if (result instanceof ArResult.Completed) {
            answer.put("outcome", "completed");
            answer.put("pointId", ((ArResult.Completed) result).getPointId());
        } else if (result instanceof ArResult.Unavailable) {
            ArResult.Unavailable unavailable = (ArResult.Unavailable) result;
            answer.put("outcome", "unavailable");
            answer.put("pointId", unavailable.getPointId());
            answer.put("reason", unavailable.getReason().name());
        } else {
            answer.put("outcome", "dismissed");
            answer.put("pointId", ((ArResult.Dismissed) result).getPointId());
        }
        call.resolve(answer);
    }

    private ArPointSpec buildSpec(PluginCall call) throws JSONException {
        String pointId = requireString(call.getString("pointId"), "pointId");
        String title = call.getString("title", "Точка маршрута");
        int stepIndex = call.getInt("stepIndex", 1);
        int stepTotal = call.getInt("stepTotal", 1);

        return new ArPointSpec(
            pointId,
            title,
            Math.max(1, Math.min(stepIndex, stepTotal)),
            Math.max(1, stepTotal),
            target(call.getObject("target")),
            companion(call.getObject("companion")),
            narration(call.getObject("narration")),
            marker(call.getObject("marker"))
        );
    }

    private ArTarget target(JSObject target) throws JSONException {
        if (target == null) {
            return null;
        }
        double lat = target.getDouble("lat");
        double lon = target.getDouble("lon");
        String label = target.getString("label", "Цель");
        return new ArTarget(new GeoPoint(lat, lon), label, target.optDouble("heightMeters", 0.0));
    }

    /**
     * Проводник появляется, только если его модель действительно лежит в
     * assets: без файла экран показал бы пустое место. `null` из приложения —
     * решение не показывать маскот (например, у братской могилы).
     */
    private CompanionSpec companion(JSObject companion) {
        if (companion == null) {
            return null;
        }
        String asset = resolveCompanionAsset(companion.getString("asset"));
        if (asset == null) {
            return null;
        }
        return new CompanionSpec(companion.getString("name", "Проводник"), companion.getString("subtitle", ""), asset);
    }

    private String resolveCompanionAsset(String requested) {
        AssetManager assets = getContext().getAssets();
        if (requested != null && assetExists(assets, requested)) {
            return requested;
        }
        // Модель кладут в assets AAR под своим именем — берём первую, какая есть.
        try {
            String[] files = assets.list(COMPANION_DIR);
            if (files != null) {
                for (String file : files) {
                    if (file.endsWith(".glb")) {
                        return COMPANION_DIR + "/" + file;
                    }
                }
            }
        } catch (IOException ignored) {
            // Папки нет — проводника не будет, экран работает и без него.
        }
        return null;
    }

    private boolean assetExists(AssetManager assets, String path) {
        try {
            assets.open(path).close();
            return true;
        } catch (IOException error) {
            return false;
        }
    }

    private NarrationSpec narration(JSObject narration) throws JSONException {
        List<SubtitleLine> lines = new ArrayList<>();
        String audioUri = null;
        // Таймкодов бэкенд не отдаёт, и приложение режет текст на глаз. Модулю
        // об этом надо сказать: он подгонит строки под длину записи, иначе
        // голос и субтитры разъедутся уже на второй фразе.
        boolean estimated = false;
        if (narration != null) {
            audioUri = narration.getString("audioUrl");
            estimated = Boolean.TRUE.equals(narration.getBoolean("subtitlesAreEstimated", false));
            JSONArray subtitles = narration.getJSONArray("subtitles");
            if (subtitles != null) {
                for (int index = 0; index < subtitles.length(); index++) {
                    JSONObject line = subtitles.getJSONObject(index);
                    long from = line.getLong("fromMs");
                    long to = line.getLong("toMs");
                    if (to > from) {
                        lines.add(new SubtitleLine(from, to, line.getString("text")));
                    }
                }
            }
        }
        return new NarrationSpec(audioUri, lines, estimated);
    }

    private MarkerSpec marker(JSObject marker) {
        if (marker == null) {
            return null;
        }
        String asset = marker.getString("asset");
        if (asset == null || !assetExists(getContext().getAssets(), asset)) {
            return null;
        }
        Double width = marker.has("widthMeters") ? marker.optDouble("widthMeters") : null;
        Long fallbackMs = marker.has("fallbackAfterMs") ? marker.optLong("fallbackAfterMs") : null;
        return new MarkerSpec(asset, width == null ? null : width.floatValue(), null, fallbackMs);
    }

    private String requireString(String value, String field) {
        if (value == null || value.isEmpty()) {
            throw new IllegalArgumentException("нет поля " + field);
        }
        return value;
    }
}
