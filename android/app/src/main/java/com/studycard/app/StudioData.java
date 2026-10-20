package com.studycard.app;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

/** Recipes use the same column IDs, modes and JSON fields as the desktop studio. */
final class StudioData {
    static final String[] ICONS = {"table_grid", "gamepad", "rocket", "bulb", "study", "library",
            "decks", "target", "globe", "audio", "star", "flame", "pencil", "headphones",
            "microphone", "music", "sound_wave", "brain", "puzzle", "compass", "leaf", "flower",
            "sun", "moon", "cloud", "bolt", "heart", "trophy", "medal", "gem", "mountain",
            "anchor"};
    static final String[] ICON_NAMES = {"Table", "Game", "Rocket", "Idea", "Cards", "Book", "Stack",
            "Target", "World", "Sound", "Star", "Flame", "Pencil", "Headphones", "Microphone",
            "Music", "Sound wave", "Brain", "Puzzle", "Compass", "Leaf", "Flower", "Sun", "Moon",
            "Cloud", "Lightning", "Heart", "Trophy", "Medal", "Gem", "Mountain", "Anchor"};
    static final String[] MODE_NAMES = {"Multiple choice", "Matching pairs", "Type the answer",
            "Listen and transcribe", "Listen and translate", "Listen and choose", "Memory cards",
            "Build the word"};
    static JSONObject copy(JSONObject value) {
        return CardStore.json(value.toString());
    }
    static JSONObject table(String name, String template, int rowCount, int columnCount) {
        JSONObject value = new JSONObject();
        CardStore.put(value, "id", CardStore.uuid());
        CardStore.put(value, "name", name);
        CardStore.put(value, "description", "");
        CardStore.put(value, "icon", "table_grid");
        String[] names = template.equals("verbs")
                ? new String[] {"Infinitive", "Past simple", "Past participle", "Meaning"}
                : template.equals("phrases")
                ? new String[] {"Phrase", "Example sentence", "Meaning"}
                : new String[] {"Word", "Meaning"};
        JSONArray columns = new JSONArray(), rows = new JSONArray();
        for (int i = 0; i < columnCount; i++) {
            JSONObject column = new JSONObject();
            CardStore.put(column, "id", CardStore.uuid());
            CardStore.put(column, "name", i < names.length ? names[i] : "Column " + (i + 1));
            boolean meaning = i < names.length && names[i].equals("Meaning");
            CardStore.put(column, "language", meaning ? "tr" : "en");
            CardStore.put(column, "speech_order", meaning ? 0 : i + 1);
            columns.put(column);
        }
        for (int i = 0; i < rowCount; i++)
            rows.put(row(Integer.toString(i + 1)));
        CardStore.put(value, "columns", columns);
        CardStore.put(value, "rows", rows);
        CardStore.put(value, "speakers", true);
        CardStore.put(value, "reading_order", "rows");
        CardStore.put(value, "speed", 1.);
        CardStore.put(value, "pause_ms", 500);
        CardStore.put(value, "repeat", 1);
        return value;
    }
    static JSONObject row(String name) {
        JSONObject row = new JSONObject();
        CardStore.put(row, "id", CardStore.uuid());
        CardStore.put(row, "name", name);
        CardStore.put(row, "cells", new JSONObject());
        CardStore.put(row, "muted", new JSONArray());
        return row;
    }
    static JSONObject game() {
        JSONObject game = new JSONObject();
        CardStore.put(game, "id", CardStore.uuid());
        CardStore.put(game, "name", "");
        CardStore.put(game, "description", "");
        CardStore.put(game, "icon", "gamepad");
        CardStore.put(game, "mode", "quiz");
        CardStore.put(game, "source", "manual");
        CardStore.put(game, "source_id", "");
        CardStore.put(game, "prompt_column", "term");
        CardStore.put(game, "answer_column", "definition");
        CardStore.put(game, "question_count", 10);
        CardStore.put(game, "time_limit", 0);
        CardStore.put(game, "shuffle", true);
        CardStore.put(game, "hints", true);
        CardStore.put(game, "sound", true);
        CardStore.put(game, "manual_pairs", new JSONArray());
        CardStore.put(game, "language", "en");
        CardStore.put(game, "answer_language", "tr");
        return game;
    }
    static void require(boolean condition, String error) {
        if (!condition)
            throw new IllegalArgumentException(error);
    }
    static void identity(JSONObject value) {
        require(!value.optString("id").isEmpty() && !value.optString("name").trim().isEmpty(),
                "Please enter a name.");
        require(Arrays.asList(ICONS).contains(value.optString("icon")), "Invalid extension icon.");
        require(value.opt("description") instanceof String, "Invalid extension identity.");
    }
    static void validateTable(JSONObject table) {
        identity(table);
        JSONArray columns = table.optJSONArray("columns"), rows = table.optJSONArray("rows");
        require(columns != null && columns.length() > 0 && columns.length() <= 64 && rows != null
                        && rows.length() <= 10000,
                "Invalid table size");
        Set<String> ids = new HashSet<>(), rowIds = new HashSet<>();
        for (int i = 0; i < columns.length(); i++) {
            JSONObject column = columns.optJSONObject(i);
            require(column != null && !column.optString("id").isEmpty()
                            && ids.add(column.optString("id"))
                            && !column.optString("name").trim().isEmpty(),
                    "Invalid column");
            require(column.opt("language") instanceof String
                            && integer(column, "speech_order", 0, 64),
                    "Invalid speech settings");
        }
        for (int i = 0; i < rows.length(); i++) {
            JSONObject row = rows.optJSONObject(i);
            require(row != null && rowIds.add(row.optString("id")) && !row.optString("id").isEmpty()
                            && row.opt("name") instanceof String,
                    "Invalid row");
            JSONObject cells = row.optJSONObject("cells");
            JSONArray muted = row.optJSONArray("muted");
            require(cells != null && muted != null, "Invalid cells");
            for (java.util.Iterator<String> keys = cells.keys(); keys.hasNext();) {
                String key = keys.next();
                require(ids.contains(key) && cells.opt(key) instanceof String, "Invalid cells");
            }
            for (int j = 0; j < muted.length(); j++)
                require(ids.contains(muted.optString(j)), "Invalid muted cells");
        }
        require(table.opt("speakers") instanceof Boolean
                        && Arrays.asList("rows", "columns")
                                .contains(table.optString("reading_order")),
                "Invalid reading order");
        require(table.optDouble("speed", 0) >= .5 && table.optDouble("speed", 0) <= 2
                        && integer(table, "repeat", 1, 10) && integer(table, "pause_ms", 0, 5000),
                "Invalid playback settings");
    }
    static boolean integer(JSONObject value, String key, int low, int high) {
        Object number = value.opt(key);
        return number instanceof Number
                && ((Number) number).doubleValue() == ((Number) number).intValue()
                && value.optInt(key) >= low && value.optInt(key) <= high;
    }
    static void validateGame(JSONObject game) {
        identity(game);
        require(Arrays.asList(GameEngine.MODES).contains(game.optString("mode"))
                        && Arrays.asList("manual", "library", "table")
                                .contains(game.optString("source")),
                "Invalid game recipe.");
        require(integer(game, "question_count", 1, 100) && integer(game, "time_limit", 0, 300),
                "Invalid game rules.");
        for (String key : new String[] {"shuffle", "hints", "sound"})
            require(game.opt(key) instanceof Boolean, "Invalid game rules.");
        for (String key : new String[] {
                     "source_id", "prompt_column", "answer_column", "language", "answer_language"})
            require(game.opt(key) instanceof String, "Invalid game recipe.");
        JSONArray pairs = game.optJSONArray("manual_pairs");
        require(pairs != null && pairs.length() <= 10000, "Invalid question pairs.");
        for (int i = 0; i < pairs.length(); i++) {
            JSONObject pair = pairs.optJSONObject(i);
            require(pair != null && pair.opt("prompt") instanceof String
                            && pair.opt("answer") instanceof String,
                    "Invalid question pairs.");
        }
    }
    static List<GameEngine.Pair> questions(CardStore store, JSONObject game) {
        validateGame(game);
        List<GameEngine.Pair> result = new ArrayList<>();
        String source = game.optString("source"), prompt = game.optString("prompt_column"),
               answer = game.optString("answer_column");
        boolean needsAnswer = !game.optString("mode").equals("audio_dictation");
        if (source.equals("manual")) {
            JSONArray rows = game.optJSONArray("manual_pairs");
            for (int i = 0; i < rows.length(); i++) {
                JSONObject row = rows.optJSONObject(i);
                result.add(new GameEngine.Pair(row.optString("prompt"), row.optString("answer"),
                        row.optString("language", game.optString("language")),
                        row.optString("answer_language", game.optString("answer_language")),
                        row.optString("card_id")));
            }
        } else if (source.equals("library")) {
            require(Arrays.asList("term", "definition").contains(prompt)
                            && (!needsAnswer
                                    || Arrays.asList("term", "definition").contains(answer)
                                            && !prompt.equals(answer)),
                    "Choose two different columns.");
            for (JSONObject card : store.list("card"))
                if (game.optString("source_id").isEmpty()
                        || game.optString("source_id").equals(card.optString("deck_uuid")))
                    result.add(new GameEngine.Pair(card.optString(prompt), card.optString(answer),
                            CardTransfer.language(card.optString(
                                    prompt.equals("term") ? "source_lang" : "target_lang",
                                    prompt.equals("term") ? "en" : "tr")),
                            CardTransfer.language(card.optString(
                                    answer.equals("term") ? "source_lang" : "target_lang",
                                    answer.equals("term") ? "en" : "tr")),
                            card.optString("uuid")));
        } else {
            JSONObject table = store.get(game.optString("source_id"));
            require(table != null && table.has("columns"),
                    "The source table is unavailable. Choose another source in the studio.");
            Map<String, JSONObject> columns = new LinkedHashMap<>();
            JSONArray cols = table.optJSONArray("columns");
            for (int i = 0; i < cols.length(); i++) {
                JSONObject col = cols.optJSONObject(i);
                columns.put(col.optString("id"), col);
            }
            require(columns.containsKey(prompt)
                            && (!needsAnswer
                                    || columns.containsKey(answer) && !prompt.equals(answer)),
                    "Choose two different columns.");
            JSONArray rows = table.optJSONArray("rows");
            for (int i = 0; i < rows.length(); i++) {
                JSONObject cells = rows.optJSONObject(i).optJSONObject("cells");
                result.add(new GameEngine.Pair(cells.optString(prompt), cells.optString(answer),
                        columns.get(prompt).optString("language"),
                        columns.getOrDefault(answer, columns.get(prompt)).optString("language")));
            }
        }
        return GameEngine.validatePool(game.optString("mode"), result);
    }
    static List<TableSpeechPlan.Utterance> speech(JSONObject table, int onlyRow) {
        List<TableSpeechPlan.Column> columns = new ArrayList<>();
        List<TableSpeechPlan.Row> rows = new ArrayList<>();
        JSONArray cs = table.optJSONArray("columns"), rs = table.optJSONArray("rows");
        for (int i = 0; i < cs.length(); i++) {
            JSONObject c = cs.optJSONObject(i);
            columns.add(new TableSpeechPlan.Column(
                    c.optString("id"), c.optString("language"), c.optInt("speech_order")));
        }
        for (int i = 0; i < rs.length(); i++)
            if (onlyRow < 0 || i == onlyRow) {
                JSONObject r = rs.optJSONObject(i), cells = r.optJSONObject("cells");
                Map<String, String> values = new LinkedHashMap<>();
                for (java.util.Iterator<String> keys = cells.keys(); keys.hasNext();) {
                    String key = keys.next();
                    values.put(key, cells.optString(key));
                }
                Set<String> muted = new HashSet<>();
                JSONArray m = r.optJSONArray("muted");
                for (int j = 0; j < m.length(); j++)
                    muted.add(m.optString(j));
                rows.add(new TableSpeechPlan.Row(values, muted));
            }
        return TableSpeechPlan.create(columns, rows,
                table.optString("reading_order").equals("columns"), table.optInt("repeat", 1));
    }
    static String menuKey(String kind, String id) {
        return "personal_menu_" + kind + "_" + id;
    }
    static String save(CardStore store, String kind, JSONObject document) {
        if (kind.equals("table"))
            validateTable(document);
        else
            validateGame(document);
        return store.saveDocument(kind, document.optString("id"), document);
    }
}
