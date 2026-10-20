package com.studycard.app;

import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;
import org.json.JSONArray;
import org.json.JSONObject;

final class SentenceExamples {
    private static volatile JSONObject offline;
    private static final MapCache translations = new MapCache();
    private static final class MapCache {
        final java.util.Map<String, String> values = new java.util.concurrent.ConcurrentHashMap<>();
        volatile boolean loaded;
    }
    private static JSONObject offline(Context context) {
        JSONObject value = offline;
        if (value == null)
            synchronized (SentenceExamples.class) {
                value = offline;
                if (value == null) {
                    try (InputStream in = context.getAssets().open("offline_usage.json")) {
                        value = new JSONObject(read(in));
                    } catch (Exception invalid) {
                        value = new JSONObject();
                    }
                    offline = value;
                }
            }
        return value;
    }
    static String translation(Context context, String sentence, String target) {
        if (!translations.loaded)
            synchronized (translations) {
                if (!translations.loaded) {
                    try (InputStream in = context.getAssets().open("offline_translations.json")) {
                        JSONObject data = new JSONObject(read(in));
                        for (java.util.Iterator<String> keys = data.keys(); keys.hasNext();) {
                            String text = keys.next();
                            JSONObject values = data.optJSONObject(text);
                            for (java.util.Iterator<String> languages = values.keys();
                                    languages.hasNext();) {
                                String code = languages.next();
                                translations.values.put(
                                        text + "\u0001" + code, values.optString(code));
                            }
                        }
                    } catch (Exception ignored) {
                    }
                    translations.loaded = true;
                }
            }
        return translations.values.getOrDefault(sentence + "\u0001" + target, "");
    }
    static Pattern pattern(String term, String language) {
        String quoted = Pattern.quote(term.trim());
        return Pattern.compile((language.equals("ja") || language.startsWith("zh"))
                        ? quoted
                        : "(?<![\\p{L}\\p{N}_])" + quoted + "(?![\\p{L}\\p{N}_])",
                Pattern.CASE_INSENSITIVE | Pattern.UNICODE_CASE);
    }
    static boolean useful(String term, String sentence, String language) {
        if (term.trim().isEmpty() || sentence.length() > 500 || sentence.endsWith("...")
                || sentence.endsWith("…"))
            return false;
        Pattern target = pattern(term, language);
        if (!target.matcher(sentence).find())
            return false;
        String context = target.matcher(sentence).replaceAll(" ");
        if (language.equals("ja") || language.startsWith("zh"))
            return sentence.replaceAll("[^\\p{L}]", "").length() >= 12
                    && context.replaceAll("[^\\p{L}]", "").length() >= 6;
        return words(sentence) >= 8 && words(context) >= 4;
    }
    private static int words(String value) {
        java.util.regex.Matcher m =
                Pattern.compile("[\\p{L}\\p{N}]+(?:['’][\\p{L}]+)*").matcher(value);
        int count = 0;
        while (m.find())
            count++;
        return count;
    }
    static List<String> local(Context context, String term, String language) {
        List<String> result = new ArrayList<>();
        try {
            JSONObject entries = offline(context).optJSONObject(language);
            JSONArray rows = entries == null ? null : entries.optJSONArray(CardStore.wordKey(term));
            if (rows != null)
                for (int i = 0; i < rows.length(); i++)
                    if (useful(term, rows.getString(i), language))
                        result.add(rows.getString(i));
        } catch (Exception ignored) {
        }
        return result;
    }
    static List<String> online(String term, String language) throws Exception {
        return online(term, language, "tr");
    }
    static List<String> online(String term, String language, String target) throws Exception {
        String code;
        switch (language) {
            case "en":
                code = "eng";
                break;
            case "tr":
                code = "tur";
                break;
            case "de":
                code = "deu";
                break;
            case "es":
                code = "spa";
                break;
            case "fr":
                code = "fra";
                break;
            case "it":
                code = "ita";
                break;
            case "pt":
                code = "por";
                break;
            case "ja":
                code = "jpn";
                break;
            case "zh":
            case "zh-tw":
                code = "cmn";
                break;
            default:
                return new ArrayList<>();
        }
        String targetCode = iso3(target);
        HttpURLConnection connection =
                (HttpURLConnection) new URL("https://api.tatoeba.org/v1/sentences?lang=" + code
                        + "&q=" + URLEncoder.encode(term, "UTF-8")
                        + "&limit=50&is_unapproved=no&is_orphan=no&showtrans:lang=" + targetCode)
                        .openConnection();
        connection.setConnectTimeout(2500);
        connection.setReadTimeout(3000);
        connection.setRequestProperty("User-Agent", "StudyCard-Android/1.1");
        List<String> result = new ArrayList<>();
        try (InputStream in = connection.getInputStream()) {
            JSONObject payload = new JSONObject(read(in));
            JSONArray rows = payload.optJSONArray("data");
            if (rows != null)
                for (int i = 0; i < rows.length() && result.size() < 10; i++) {
                    JSONObject row = rows.optJSONObject(i);
                    if (row == null || !code.equals(row.optString("lang")))
                        continue;
                    String value = row.optString("text");
                    if (useful(term, value, language) && !result.contains(value)) {
                        result.add(value);
                        JSONArray groups = row.optJSONArray("translations");
                        if (groups != null)
                            for (int j = 0; j < groups.length(); j++) {
                                JSONArray group = groups.optJSONArray(j);
                                if (group == null) {
                                    JSONObject one = groups.optJSONObject(j);
                                    group = new JSONArray();
                                    if (one != null)
                                        group.put(one);
                                }
                                for (int k = 0; k < group.length(); k++) {
                                    JSONObject translated = group.optJSONObject(k);
                                    if (translated != null
                                            && targetCode.equals(translated.optString("lang"))
                                            && !translated.optString("text").isEmpty())
                                        translations.values.putIfAbsent(value + "\u0001" + target,
                                                translated.optString("text"));
                                }
                            }
                    }
                }
        } finally {
            connection.disconnect();
        }
        return result;
    }
    private static String iso3(String language) {
        switch (language) {
            case "en":
                return "eng";
            case "tr":
                return "tur";
            case "de":
                return "deu";
            case "es":
                return "spa";
            case "fr":
                return "fra";
            case "it":
                return "ita";
            case "pt":
                return "por";
            case "ja":
                return "jpn";
            case "zh":
            case "zh-tw":
                return "cmn";
            default:
                return language;
        }
    }
    static String read(InputStream stream) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int count;
        while ((count = stream.read(buffer)) != -1) {
            out.write(buffer, 0, count);
            if (out.size() > 4000000)
                throw new IllegalArgumentException("File too large");
        }
        return out.toString("UTF-8");
    }
}
