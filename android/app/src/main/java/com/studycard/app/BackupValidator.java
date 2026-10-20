package com.studycard.app;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

/** Validate all data and preferences before a restore transaction changes anything. */
final class BackupValidator {
    void check(JSONObject backup) {
        StudioData.require(backup.optString("format").equals("studycard-android-device-backup")
                        && backup.optInt("version") == 1,
                "Unsupported backup format");
        JSONObject tables = backup.optJSONObject("tables");
        StudioData.require(tables != null, "Invalid backup contents");
        JSONArray items = tables.optJSONArray("items"), config = tables.optJSONArray("config"),
                  recovery = tables.optJSONArray("recovery");
        StudioData.require(items != null && config != null && recovery != null
                        && items.length() <= 200000 && config.length() <= 10000
                        && recovery.length() <= 200000,
                "Backup is too large");
        Set<String> ids = new HashSet<>(), decks = new HashSet<>();
        for (int i = 0; i < items.length(); i++) {
            JSONObject row = items.optJSONObject(i);
            StudioData.require(row != null && row.opt("uuid") instanceof String
                            && row.opt("data") instanceof String
                            && row.opt("entity") instanceof String && ids.add(row.optString("uuid"))
                            && !row.optString("uuid").isEmpty(),
                    "Invalid backup items");
            JSONObject doc = CardStore.json(row.optString("data"));
            String entity = row.optString("entity");
            if (entity.equals("deck") && row.optInt("deleted") == 0) {
                StudioData.require(!doc.optString("name").trim().isEmpty(), "Invalid deck name");
                decks.add(row.optString("uuid"));
            }
            if (entity.equals("table")) {
                StudioData.validateTable(doc);
                StudioData.require(row.optString("uuid").equals(doc.optString("id")),
                        "Invalid table identity");
            }
            if (entity.equals("game")) {
                StudioData.validateGame(doc);
                StudioData.require(
                        row.optString("uuid").equals(doc.optString("id")), "Invalid game identity");
            }
            if (entity.equals("practice"))
                StudioData.require(Arrays.asList(0, 1).contains(doc.optInt("correct", -1))
                                && !doc.optString("mode").isEmpty()
                                && doc.opt("answer") instanceof String
                                && doc.opt("expected") instanceof String
                                && doc.opt("day") instanceof String,
                        "Invalid practice history");
            if (entity.equals("game_run"))
                StudioData.require(!doc.optString("game_id").isEmpty()
                                && StudioData.integer(doc, "total", 1, 100)
                                && StudioData.integer(doc, "correct", 0, doc.optInt("total"))
                                && Double.isFinite(doc.optDouble("duration_seconds", -1))
                                && doc.optDouble("duration_seconds", -1) >= 0,
                        "Invalid game history");
            if (entity.equals("review"))
                StudioData.require(StudioData.integer(doc, "rating", 1, 3)
                                && doc.opt("reviewed_at") instanceof String,
                        "Invalid review history");
            if (entity.equals("timer"))
                StudioData.require(
                        Arrays.asList("timer", "stopwatch").contains(doc.optString("mode"))
                                && doc.optLong("duration_seconds", -1) >= 0
                                && doc.opt("created_at") instanceof String,
                        "Invalid focus history");
            if (entity.equals("sentence"))
                StudioData.require(!doc.optString("lang").isEmpty()
                                && doc.opt("term_key") instanceof String
                                && doc.opt("text") instanceof String
                                && doc.optJSONObject("translations") != null,
                        "Invalid sentence memory");
        }
        for (int i = 0; i < items.length(); i++) {
            JSONObject row = items.optJSONObject(i), doc = CardStore.json(row.optString("data"));
            if (row.optString("entity").equals("card") && row.optInt("deleted") == 0) {
                StudioData.require(decks.contains(doc.optString("deck_uuid"))
                                && !doc.optString("term").trim().isEmpty()
                                && !doc.optString("definition").trim().isEmpty()
                                && Arrays.asList("new", "learning", "mastered")
                                        .contains(doc.optString("status", "new")),
                        "Invalid card data");
                try {
                    LocalDate.parse(doc.optString("due_date", LocalDate.now().toString()));
                } catch (java.time.DateTimeException invalid) {
                    throw new IllegalArgumentException("Invalid card review date");
                }
            }
        }
        Set<String> keys = new HashSet<>();
        for (int i = 0; i < config.length(); i++) {
            JSONObject row = config.optJSONObject(i);
            StudioData.require(row != null && row.opt("key") instanceof String
                            && row.opt("value") instanceof String && keys.add(row.optString("key")),
                    "Invalid backup preferences");
            preference(row.optString("key"), row.optString("value"));
        }
    }
    private void preference(String key, String value) {
        if (key.startsWith("personal_menu_") || key.startsWith("menu_visible_")
                || key.startsWith("plugin_")
                || Arrays
                        .asList("sfx_enabled", "auto_pronounce", "reduced_motion", "show_phonetics",
                                "show_card_notes", "shuffle_cards", "practice_auto_next",
                                "practice_autoplay", "audio_prefetch", "keep_screen_on",
                                "daily_notification_enabled")
                        .contains(key))
            StudioData.require(value.equals("true") || value.equals("false"),
                    "Invalid backup menu preferences");
        if (key.equals("notification_time"))
            StudioData.require(
                    value.matches("([01][0-9]|2[0-3]):[0-5][0-9]"), "Invalid backup preferences");
        String[][] enums = {{"ui_language", "tr", "en", "de", "es"},
                {"theme", "dark_slate", "midnight", "graphite"},
                {"accent_color", "#10b981", "#38bdf8", "#a78bfa", "#fbbf24", "#fb7185"},
                {"startup_page", "study", "library", "tables", "stats", "import", "settings"},
                {"pronounce_trigger", "appear", "flip", "both"}};
        for (String[] values : enums)
            if (key.equals(values[0]))
                StudioData.require(Arrays.asList(values).subList(1, values.length).contains(value),
                        "Invalid backup preferences");
        if (key.equals("profile_name"))
            StudioData.require(value.length() <= 40, "Invalid backup preferences");
        String[] names = {"text_scale", "daily_goal", "session_size", "practice_advance_ms",
                "speech_volume", "sfx_volume", "speech_speed", "focus_goal_hours"};
        double[] low = {90, 5, 5, 300, 0, 0, .5, 1},
                 high = {130, 100, 200, 5000, 100, 100, 2, 50000};
        for (int i = 0; i < names.length; i++)
            if (key.equals(names[i])) {
                try {
                    double number = Double.parseDouble(value);
                    StudioData.require(Double.isFinite(number) && number >= low[i]
                                    && number <= high[i]
                                    && (key.equals("speech_speed")
                                            || number == (int) number && value.matches("[0-9]+")),
                            "Invalid backup preferences");
                } catch (NumberFormatException invalid) {
                    throw new IllegalArgumentException("Invalid backup preferences");
                }
            }
    }
}
