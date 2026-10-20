package com.studycard.app;

import android.content.Context;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import org.json.JSONArray;
import org.json.JSONObject;

/** Optional dictionary assistance. Manual input and all saved cards work offline. */
final class WordLookup {
    static JSONObject find(Context context, String word, String source, String target)
            throws Exception {
        JSONObject result = new JSONObject();
        try (InputStream in = context.getAssets().open("offline_words.json")) {
            JSONObject words = new JSONObject(SentenceExamples.read(in));
            JSONObject local = words.optJSONObject(CardStore.wordKey(word));
            if (local != null && source.equals("en")) {
                if (target.equals("tr"))
                    CardStore.put(result, "definition", local.optString("definition"));
                CardStore.put(result, "phonetic", local.optString("phonetic"));
            }
        }
        if (!result.has("definition"))
            try {
                JSONObject response =
                        new JSONObject(get("https://api.mymemory.translated.net/get?q="
                                + URLEncoder.encode(word, "UTF-8") + "&langpair="
                                + URLEncoder.encode(source + "|" + target, "UTF-8")));
                JSONObject data = response.optJSONObject("responseData");
                String meaning = data == null ? "" : data.optString("translatedText");
                if (response.optInt("responseStatus") == 200 && !meaning.isEmpty()
                        && !meaning.toUpperCase(java.util.Locale.ROOT)
                                .startsWith("MYMEMORY WARNING"))
                    CardStore.put(result, "definition", meaning);
            } catch (Exception unavailable) {
                if (result.length() == 0 && !source.equals("en"))
                    throw unavailable;
            }
        if (source.equals("en"))
            try {
                JSONArray entries =
                        new JSONArray(get("https://api.dictionaryapi.dev/api/v2/entries/en/"
                                + URLEncoder.encode(word, "UTF-8")));
                JSONObject entry = entries.optJSONObject(0);
                if (entry != null) {
                    String phonetic = entry.optString("phonetic");
                    JSONArray sounds = entry.optJSONArray("phonetics");
                    if (phonetic.isEmpty() && sounds != null)
                        for (int i = 0; i < sounds.length(); i++)
                            if (sounds.optJSONObject(i) != null
                                    && !sounds.optJSONObject(i).optString("text").isEmpty()) {
                                phonetic = sounds.optJSONObject(i).optString("text");
                                break;
                            }
                    if (!phonetic.isEmpty())
                        CardStore.put(result, "phonetic", phonetic);
                    JSONArray meanings = entry.optJSONArray("meanings");
                    if (meanings != null && meanings.length() > 0) {
                        JSONObject meaning = meanings.optJSONObject(0);
                        CardStore.put(result, "part_of_speech",
                                meaning.optString("partOfSpeech", "word"));
                        JSONArray definitions = meaning.optJSONArray("definitions");
                        if (target.equals("en") && definitions != null && definitions.length() > 0)
                            CardStore.put(result, "definition",
                                    definitions.optJSONObject(0).optString("definition"));
                    }
                }
            } catch (Exception unavailable) {
            }
        return result;
    }
    private static String get(String url) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setConnectTimeout(3000);
        connection.setReadTimeout(4000);
        connection.setRequestProperty("User-Agent", "Studycard-Android/1.1");
        try (InputStream in = connection.getInputStream()) {
            return SentenceExamples.read(in);
        } finally {
            connection.disconnect();
        }
    }
}
