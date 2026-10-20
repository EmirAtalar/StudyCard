package com.studycard.app;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/** Explicit interface translations; vocabulary and deck content stay untouched. */
final class L10n {
    private final Map<String, JSONArray> entries = new HashMap<>();
    private String language;
    L10n(Context context, String language) {
        this.language = language;
        try (InputStream stream = context.getAssets().open("ui_catalog.json")) {
            ByteArrayOutputStream output = new ByteArrayOutputStream(); byte[] buffer = new byte[4096]; int count;
            while ((count = stream.read(buffer)) != -1) output.write(buffer,0,count);
            JSONObject data = new JSONObject(output.toString("UTF-8")); Iterator<String> keys = data.keys();
            while (keys.hasNext()) { String key = keys.next(); JSONArray row = data.getJSONArray(key); entries.put(key,row); for (int i=0;i<row.length();i++) entries.putIfAbsent(row.getString(i),row); }
        } catch (Exception error) { throw new IllegalStateException("Missing interface translations",error); }
    }
    String get(String key, Object... values) {
        JSONArray row = entries.get(key); int index = "tr".equals(language) ? 0 : "de".equals(language) ? 2 : "es".equals(language) ? 3 : 1;
        String text = row == null ? key : row.optString(index,key);
        for (int i=0;i+1<values.length;i+=2) text = text.replace("{"+values[i]+"}",String.valueOf(values[i+1]));
        return text;
    }
}
