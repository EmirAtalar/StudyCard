package com.studycard.app;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import org.json.JSONArray;
import org.json.JSONObject;

/** Full desktop .studycard interchange, including history and stable studio identities. */
final class DesktopBackup {
    private static final String[] CORE = {
            "decks", "cards", "study_logs", "timer_sessions", "practice_attempts"};
    static JSONObject read(Context context, InputStream input) throws Exception {
        File file = File.createTempFile("studycard-desktop-", ".sqlite", context.getCacheDir());
        Map<String, String> json = new LinkedHashMap<>();
        Set<String> entries = new HashSet<>();
        try {
            try (ZipInputStream zip = new ZipInputStream(input)) {
                ZipEntry entry;
                byte[] buffer = new byte[8192];
                while ((entry = zip.getNextEntry()) != null) {
                    String name = entry.getName();
                    if (!Arrays.asList("library.sqlite", "settings.json", "manifest.json")
                                    .contains(name)
                            || !entries.add(name) || entry.isDirectory())
                        throw new IllegalArgumentException("Invalid backup contents");
                    long size = 0,
                         limit = name.equals("library.sqlite") ? 256L * 1024 * 1024 : 1024 * 1024;
                    ByteArrayOutputStream text = new ByteArrayOutputStream();
                    try (OutputStream out = name.equals("library.sqlite")
                                    ? new FileOutputStream(file)
                                    : text) {
                        int count;
                        while ((count = zip.read(buffer)) != -1) {
                            size += count;
                            if (size > limit)
                                throw new IllegalArgumentException("Backup is too large");
                            out.write(buffer, 0, count);
                        }
                    }
                    if (!name.equals("library.sqlite"))
                        json.put(name, text.toString("UTF-8"));
                    zip.closeEntry();
                }
            }
            if (entries.size() != 3)
                throw new IllegalArgumentException("Incomplete backup database");
            JSONObject manifest = new JSONObject(json.get("manifest.json")),
                       preferences = new JSONObject(json.get("settings.json"));
            StudioData.require(manifest.optString("format").equals("studycard-device-backup")
                            && manifest.optInt("version") == 1,
                    "Unsupported backup format");
            JSONObject backup = new JSONObject(), tables = new JSONObject();
            JSONArray items = new JSONArray(), config = new JSONArray();
            CardStore.put(backup, "format", "studycard-android-device-backup");
            CardStore.put(backup, "version", 1);
            CardStore.put(backup, "created_at", manifest.optString("created_at"));
            CardStore.put(backup, "tables", tables);
            CardStore.put(tables, "items", items);
            CardStore.put(tables, "config", config);
            CardStore.put(tables, "recovery", new JSONArray());
            Map<String, String> decks = new LinkedHashMap<>(), cards = new LinkedHashMap<>();
            try (SQLiteDatabase db = SQLiteDatabase.openDatabase(
                         file.getPath(), null, SQLiteDatabase.OPEN_READONLY)) {
                try (Cursor check = db.rawQuery("PRAGMA integrity_check", null)) {
                    StudioData.require(check.moveToFirst() && check.getString(0).equals("ok"),
                            "Damaged backup database");
                }
                try (Cursor check = db.rawQuery("PRAGMA foreign_key_check", null)) {
                    StudioData.require(!check.moveToFirst(), "Damaged backup database");
                }
                Set<String> schema = new HashSet<>();
                try (Cursor cursor = db.rawQuery(
                             "SELECT name FROM sqlite_master WHERE type='table'", null)) {
                    while (cursor.moveToNext())
                        schema.add(cursor.getString(0));
                }
                JSONObject counts = manifest.getJSONObject("counts");
                for (String name : CORE) {
                    StudioData.require(schema.contains(name), "Incomplete backup database");
                    try (Cursor count = db.rawQuery("SELECT COUNT(*) FROM " + name, null)) {
                        count.moveToFirst();
                        StudioData.require(count.getLong(0) == counts.getLong(name)
                                        && count.getLong(0) <= 200000,
                                "Backup counts do not match");
                    }
                }
                Map<String, String> identities = new LinkedHashMap<>();
                if (schema.contains("sync_items"))
                    for (JSONObject identity : rows(db, "sync_items"))
                        if (identity.optInt("deleted") == 0
                                && !identity.optString("uuid").isEmpty())
                            identities.put(identity.optString("entity") + ":"
                                            + identity.optString("local_id"),
                                    identity.optString("uuid"));
                for (JSONObject deck : rows(db, "decks")) {
                    String old = deck.optString("id"),
                           id = identities.getOrDefault("deck:" + old, CardStore.uuid());
                    decks.put(old, id);
                    deck.remove("id");
                    add(items, "deck", id, deck);
                }
                for (JSONObject card : rows(db, "cards")) {
                    String old = card.optString("id"),
                           id = identities.getOrDefault("card:" + old, CardStore.uuid()),
                           deck = decks.get(card.optString("deck_id"));
                    StudioData.require(deck != null, "Invalid card deck");
                    cards.put(old, id);
                    card.remove("id");
                    card.remove("deck_id");
                    CardStore.put(card, "deck_uuid", deck);
                    cardLanguage(context, card, "source_lang");
                    cardLanguage(context, card, "target_lang");
                    add(items, "card", id, card);
                }
                for (JSONObject review : rows(db, "study_logs")) {
                    CardStore.put(review, "card_uuid",
                            cards.getOrDefault(review.optString("card_id"), ""));
                    review.remove("id");
                    review.remove("card_id");
                    add(items, "review", CardStore.uuid(), review);
                }
                for (JSONObject practice : rows(db, "practice_attempts")) {
                    CardStore.put(practice, "card_uuid",
                            cards.getOrDefault(practice.optString("card_id"), ""));
                    practice.remove("id");
                    practice.remove("card_id");
                    add(items, "practice", CardStore.uuid(), practice);
                }
                for (JSONObject timer : rows(db, "timer_sessions")) {
                    timer.remove("id");
                    add(items, "timer", CardStore.uuid(), timer);
                }
                if (schema.contains("quiz_mistakes"))
                    for (JSONObject mistake : rows(db, "quiz_mistakes")) {
                        CardStore.put(mistake, "card_uuid",
                                cards.getOrDefault(mistake.optString("card_id"), ""));
                        mistake.remove("id");
                        mistake.remove("card_id");
                        add(items, "mistake", CardStore.uuid(), mistake);
                    }
                for (String kind : new String[] {"table", "game"})
                    if (schema.contains("custom_" + (kind.equals("table") ? "tables" : "games")))
                        for (JSONObject row :
                                rows(db, "custom_" + (kind.equals("table") ? "tables" : "games"))) {
                            JSONObject doc = new JSONObject(row.getString("data"));
                            if (!doc.has("description"))
                                CardStore.put(doc, "description", "");
                            if (!doc.has("icon"))
                                CardStore.put(doc, "icon",
                                        kind.equals("table") ? "table_grid" : "gamepad");
                            if (kind.equals("game")) {
                                if (!doc.has("answer_language"))
                                    CardStore.put(doc, "answer_language", "tr");
                                if (doc.optString("source").equals("library"))
                                    CardStore.put(doc, "source_id",
                                            doc.optString("source_id").isEmpty()
                                                    ? ""
                                                    : decks.getOrDefault(doc.optString("source_id"),
                                                              "missing-desktop-deck-"
                                                                      + doc.optString(
                                                                              "source_id")));
                                StudioData.validateGame(doc);
                            } else
                                StudioData.validateTable(doc);
                            add(items, kind, doc.optString("id"), doc);
                        }
                if (schema.contains("custom_game_runs"))
                    for (JSONObject run : rows(db, "custom_game_runs")) {
                        run.remove("id");
                        add(items, "game_run", CardStore.uuid(), run);
                    }
                if (schema.contains("sentence_memory"))
                    for (JSONObject sentence : rows(db, "sentence_memory")) {
                        CardStore.put(sentence, "translations",
                                new JSONObject(sentence.optString("translations", "{}")));
                        String id = CardStore.sentencePrefix(sentence.optString("term_key"),
                                            sentence.optString("lang"))
                                + CardStore.uuidFor(sentence.optString("text") + "-"
                                        + sentence.optInt("position"));
                        add(items, "sentence", id, sentence);
                    }
                if (schema.contains("sentence_fetches"))
                    for (JSONObject fetched : rows(db, "sentence_fetches"))
                        add(items, "sentence_fetch", CardStore.uuid(), fetched);
                if (schema.contains("daily_challenges"))
                    for (JSONObject challenge : rows(db, "daily_challenges")) {
                        JSONArray old = new JSONArray(challenge.optString("card_ids", "[]")),
                                  mapped = new JSONArray();
                        for (int i = 0; i < old.length(); i++)
                            if (cards.containsKey(old.optString(i)))
                                mapped.put(cards.get(old.optString(i)));
                        CardStore.put(challenge, "card_ids", mapped);
                        add(items, "challenge", CardStore.uuid(), challenge);
                    }
            }
            for (java.util.Iterator<String> keys = preferences.keys(); keys.hasNext();) {
                String key = keys.next();
                if (excluded(key)
                        || Arrays.asList("initialized", "review_day", "review_count").contains(key))
                    continue;
                JSONObject row = new JSONObject();
                CardStore.put(row, "key", key);
                CardStore.put(row, "value", preferences.get(key).toString());
                config.put(row);
            }
            int todayCount = 0;
            for (int i = 0; i < items.length(); i++) {
                JSONObject row = items.optJSONObject(i);
                if (row.optString("entity").equals("review")
                        && CardStore.json(row.optString("data"))
                                .optString("reviewed_at")
                                .startsWith(java.time.LocalDate.now().toString()))
                    todayCount++;
            }
            JSONObject day = new JSONObject();
            CardStore.put(day, "key", "review_day");
            CardStore.put(day, "value", java.time.LocalDate.now().toString());
            config.put(day);
            JSONObject counter = new JSONObject();
            CardStore.put(counter, "key", "review_count");
            CardStore.put(counter, "value", Integer.toString(todayCount));
            config.put(counter);
            JSONObject initialized = new JSONObject();
            CardStore.put(initialized, "key", "initialized");
            CardStore.put(initialized, "value", "1");
            config.put(initialized);
            new BackupValidator().check(backup);
            return backup;
        } finally {
            file.delete();
            new File(file.getPath() + "-journal").delete();
            new File(file.getPath() + "-wal").delete();
            new File(file.getPath() + "-shm").delete();
        }
    }
    private static final Map<String, String> languages =
            new java.util.concurrent.ConcurrentHashMap<>();
    private static void cardLanguage(Context context, JSONObject card, String key)
            throws Exception {
        if (languages.isEmpty())
            synchronized (languages) {
                if (languages.isEmpty())
                    try (InputStream in = context.getAssets().open("languages.json")) {
                        JSONArray data = new JSONArray(SentenceExamples.read(in));
                        for (int i = 0; i < data.length(); i++) {
                            JSONObject language = data.optJSONObject(i);
                            for (String locale : new String[] {"tr", "en", "de", "es", "code"})
                                languages.put(
                                        language.optString(locale), language.optString("code"));
                        }
                    }
            }
        String raw = card.optString(key, key.equals("source_lang") ? "en" : "tr");
        CardStore.put(card, key, languages.getOrDefault(raw, raw));
    }
    private static boolean excluded(String key) {
        return key.contains("account") || key.contains("token")
                || key.matches("^(google_|firebase_|sync_|cloud_|ai_|ollama_).*")
                || Arrays.asList("app_shortcut", "autostart_enabled", "run_in_background",
                                 "timer_running", "timer_started", "timer_elapsed")
                           .contains(key);
    }
    private static void add(JSONArray items, String entity, String id, JSONObject data) {
        JSONObject row = new JSONObject();
        CardStore.put(row, "entity", entity);
        CardStore.put(row, "uuid", id);
        CardStore.put(row, "data", data.toString());
        CardStore.put(row, "baseline", "{}");
        CardStore.put(row, "dirty", 0);
        CardStore.put(row, "deleted", 0);
        CardStore.put(row, "generation", 1);
        CardStore.put(row, "revision", 0);
        items.put(row);
    }
    private static java.util.List<JSONObject> rows(SQLiteDatabase db, String name) {
        java.util.List<JSONObject> rows = new java.util.ArrayList<>();
        try (Cursor cursor = db.rawQuery("SELECT * FROM " + name, null)) {
            while (cursor.moveToNext()) {
                StudioData.require(rows.size() < 200000, "Backup is too large");
                JSONObject row = new JSONObject();
                for (int i = 0; i < cursor.getColumnCount(); i++) {
                    Object value = cursor.isNull(i)                          ? JSONObject.NULL
                            : cursor.getType(i) == Cursor.FIELD_TYPE_INTEGER ? cursor.getLong(i)
                            : cursor.getType(i) == Cursor.FIELD_TYPE_FLOAT   ? cursor.getDouble(i)
                                                                             : cursor.getString(i);
                    CardStore.put(row, cursor.getColumnName(i), value);
                }
                rows.add(row);
            }
        }
        return rows;
    }

    static void write(Context context, CardStore store, OutputStream output) throws Exception {
        JSONObject nativeBackup = store.deviceBackup();
        new BackupValidator().check(nativeBackup);
        File file = File.createTempFile("studycard-export-", ".sqlite", context.getCacheDir());
        Map<String, Integer> decks = new LinkedHashMap<>(), cards = new LinkedHashMap<>();
        JSONObject counts = new JSONObject();
        try {
            try (SQLiteDatabase db = SQLiteDatabase.openOrCreateDatabase(file, null)) {
                schema(db);
                db.beginTransaction();
                try {
                    int next = 1;
                    Set<String> names = new HashSet<>();
                    for (JSONObject deck : store.list("deck")) {
                        JSONObject row = StudioData.copy(deck);
                        String id = row.optString("uuid"), name = row.optString("name"),
                               unique = name;
                        int suffix = 2;
                        while (!names.add(unique))
                            unique = name + " (" + (suffix++) + ")";
                        row.remove("uuid");
                        CardStore.put(row, "name", unique);
                        CardStore.put(row, "id", next);
                        decks.put(id, next++);
                        insert(db, "decks", row);
                        syncIdentity(db, "deck", decks.get(id), id);
                    }
                    next = 1;
                    for (JSONObject card : store.list("card")) {
                        JSONObject row = StudioData.copy(card);
                        String id = row.optString("uuid");
                        Integer deck = decks.get(row.optString("deck_uuid"));
                        StudioData.require(deck != null, "Invalid card deck");
                        row.remove("uuid");
                        row.remove("deck_uuid");
                        CardStore.put(row, "id", next);
                        CardStore.put(row, "deck_id", deck);
                        cards.put(id, next++);
                        insert(db, "cards", row);
                        syncIdentity(db, "card", cards.get(id), id);
                    }
                    for (JSONObject log : store.list("review")) {
                        JSONObject row = StudioData.copy(log);
                        row.remove("uuid");
                        CardStore.put(row, "card_id", cards.get(row.optString("card_uuid")));
                        row.remove("card_uuid");
                        insert(db, "study_logs", row);
                    }
                    for (JSONObject log : store.list("practice")) {
                        JSONObject row = StudioData.copy(log);
                        row.remove("uuid");
                        CardStore.put(row, "card_id", cards.get(row.optString("card_uuid")));
                        row.remove("card_uuid");
                        insert(db, "practice_attempts", row);
                    }
                    for (JSONObject log : store.list("timer")) {
                        JSONObject row = StudioData.copy(log);
                        row.remove("uuid");
                        insert(db, "timer_sessions", row);
                    }
                    for (String kind : new String[] {"table", "game"})
                        for (JSONObject document : store.list(kind)) {
                            JSONObject data = StudioData.copy(document);
                            data.remove("uuid");
                            if (kind.equals("game") && data.optString("source").equals("library")) {
                                String source = data.optString("source_id");
                                if (!source.isEmpty())
                                    StudioData.require(decks.containsKey(source),
                                            "The source deck is unavailable.");
                                CardStore.put(data, "source_id",
                                        source.isEmpty() ? ""
                                                         : Integer.toString(decks.get(source)));
                            }
                            JSONObject row = new JSONObject();
                            CardStore.put(row, "id", data.optString("id"));
                            CardStore.put(row, "name", data.optString("name"));
                            CardStore.put(row, "data", data.toString());
                            insert(db, kind.equals("table") ? "custom_tables" : "custom_games",
                                    row);
                        }
                    for (JSONObject run : store.list("game_run")) {
                        JSONObject row = StudioData.copy(run);
                        row.remove("uuid");
                        insert(db, "custom_game_runs", row);
                    }
                    Map<String, Integer> positions = new LinkedHashMap<>();
                    for (JSONObject memory : store.list("sentence")) {
                        JSONObject row = StudioData.copy(memory);
                        row.remove("uuid");
                        CardStore.put(row, "translations",
                                row.optJSONObject("translations") == null
                                        ? "{}"
                                        : row.optJSONObject("translations").toString());
                        String key = row.optString("lang") + "\u0001" + row.optString("term_key");
                        CardStore.put(row, "position", positions.getOrDefault(key, 0));
                        positions.put(key, positions.getOrDefault(key, 0) + 1);
                        insert(db, "sentence_memory", row);
                    }
                    for (JSONObject fetched : store.list("sentence_fetch")) {
                        JSONObject row = StudioData.copy(fetched);
                        row.remove("uuid");
                        insert(db, "sentence_fetches", row);
                    }
                    for (JSONObject challenge : store.list("challenge")) {
                        JSONObject row = StudioData.copy(challenge);
                        row.remove("uuid");
                        JSONArray old = row.optJSONArray("card_ids"), mapped = new JSONArray();
                        if (old != null)
                            for (int i = 0; i < old.length(); i++)
                                if (cards.containsKey(old.optString(i)))
                                    mapped.put(cards.get(old.optString(i)));
                        CardStore.put(row, "card_ids", mapped.toString());
                        if (!row.has("filter_key"))
                            CardStore.put(row, "filter_key", "");
                        insert(db, "daily_challenges", row);
                    }
                    Map<String, JSONObject> mistakes = new LinkedHashMap<>();
                    for (JSONObject mistake : store.list("mistake"))
                        mistakes.put(mistake.optString("term"), StudioData.copy(mistake));
                    Map<String, Integer> errors = new LinkedHashMap<>();
                    for (JSONObject attempt : store.list("practice"))
                        if (attempt.optInt("correct") == 0
                                && !attempt.optBoolean("mistake_cleared")) {
                            JSONObject card = store.get(attempt.optString("card_uuid"));
                            if (card == null)
                                continue;
                            String term = card.optString("term");
                            errors.put(term, errors.getOrDefault(term, 0) + 1);
                            if (!mistakes.containsKey(term)) {
                                JSONObject row = new JSONObject();
                                CardStore.put(row, "term", term);
                                CardStore.put(row, "definition", card.optString("definition"));
                                CardStore.put(row, "card_uuid", card.optString("uuid"));
                                CardStore.put(
                                        row, "last_mistake_at", attempt.optString("practiced_at"));
                                mistakes.put(term, row);
                            }
                        }
                    for (Map.Entry<String, JSONObject> entry : mistakes.entrySet()) {
                        JSONObject row = entry.getValue();
                        row.remove("uuid");
                        CardStore.put(row, "wrong_count",
                                Math.max(row.optInt("wrong_count", 1),
                                        errors.getOrDefault(entry.getKey(), 0)));
                        CardStore.put(row, "card_id", cards.get(row.optString("card_uuid")));
                        row.remove("card_uuid");
                        insert(db, "quiz_mistakes", row);
                    }
                    db.setTransactionSuccessful();
                } finally {
                    db.endTransaction();
                }
                for (String name : CORE)
                    try (Cursor count = db.rawQuery("SELECT COUNT(*) FROM " + name, null)) {
                        count.moveToFirst();
                        CardStore.put(counts, name, count.getLong(0));
                    }
            }
            JSONObject preferences = new JSONObject();
            JSONArray configs = nativeBackup.getJSONObject("tables").getJSONArray("config");
            for (int i = 0; i < configs.length(); i++) {
                JSONObject row = configs.optJSONObject(i);
                String key = row.optString("key"), value = row.optString("value");
                if (excluded(key) || key.equals("initialized") || key.startsWith("timer_")
                        || key.startsWith("widget_") || key.startsWith("review_"))
                    continue;
                Object typed = value;
                if (value.equals("true") || value.equals("false"))
                    typed = Boolean.valueOf(value);
                else if (Arrays.asList("daily_goal", "session_size", "practice_advance_ms",
                                       "speech_volume", "sfx_volume", "text_scale",
                                       "focus_goal_hours")
                                 .contains(key))
                    typed = Integer.parseInt(value);
                else if (key.equals("speech_speed"))
                    typed = Double.parseDouble(value);
                CardStore.put(preferences, key, typed);
            }
            JSONObject manifest = new JSONObject();
            CardStore.put(manifest, "format", "studycard-device-backup");
            CardStore.put(manifest, "version", 1);
            CardStore.put(manifest, "created_at", LocalDateTime.now().toString());
            CardStore.put(manifest, "counts", counts);
            try (ZipOutputStream zip = new ZipOutputStream(output)) {
                zip.putNextEntry(new ZipEntry("library.sqlite"));
                try (InputStream in = new FileInputStream(file)) {
                    byte[] bytes = new byte[8192];
                    int n;
                    while ((n = in.read(bytes)) != -1)
                        zip.write(bytes, 0, n);
                }
                zip.closeEntry();
                jsonEntry(zip, "manifest.json", manifest);
                jsonEntry(zip, "settings.json", preferences);
            }
        } finally {
            file.delete();
            new File(file.getPath() + "-journal").delete();
        }
    }
    private static void jsonEntry(ZipOutputStream zip, String name, JSONObject value)
            throws Exception {
        zip.putNextEntry(new ZipEntry(name));
        zip.write(value.toString().getBytes(StandardCharsets.UTF_8));
        zip.closeEntry();
    }
    private static void insert(SQLiteDatabase db, String name, JSONObject row) {
        Set<String> columns = new HashSet<>();
        try (Cursor info = db.rawQuery("PRAGMA table_info(" + name + ")", null)) {
            while (info.moveToNext())
                columns.add(info.getString(1));
        }
        ContentValues values = new ContentValues();
        for (java.util.Iterator<String> keys = row.keys(); keys.hasNext();) {
            String key = keys.next();
            if (!columns.contains(key))
                continue;
            Object value = row.opt(key);
            if (value == null || value == JSONObject.NULL)
                values.putNull(key);
            else if (value instanceof Float || value instanceof Double)
                values.put(key, ((Number) value).doubleValue());
            else if (value instanceof Number)
                values.put(key, ((Number) value).longValue());
            else
                values.put(key, value.toString());
        }
        db.insertOrThrow(name, null, values);
    }
    private static void syncIdentity(SQLiteDatabase db, String entity, int localId, String id) {
        JSONObject identity = new JSONObject();
        CardStore.put(identity, "entity", entity);
        CardStore.put(identity, "local_id", localId);
        CardStore.put(identity, "uuid", id);
        insert(db, "sync_items", identity);
    }
    private static void schema(SQLiteDatabase db) {
        String[] sql = {
                "CREATE TABLE decks(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,description TEXT,icon TEXT DEFAULT '',color TEXT DEFAULT '#10b981',created_at TEXT)",
                "CREATE TABLE cards(id INTEGER PRIMARY KEY,deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,term TEXT NOT NULL,definition TEXT NOT NULL,part_of_speech TEXT,source_lang TEXT,target_lang TEXT,example_sentence TEXT,example_translation TEXT,phonetic TEXT,notes TEXT,status TEXT,is_favorite INTEGER,repetition_count INTEGER,interval_days INTEGER,ease_factor REAL,due_date TEXT,last_reviewed TEXT,created_at TEXT)",
                "CREATE TABLE study_logs(id INTEGER PRIMARY KEY,card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,rating INTEGER NOT NULL,reviewed_at TEXT)",
                "CREATE TABLE timer_sessions(id INTEGER PRIMARY KEY,mode TEXT NOT NULL,duration_seconds INTEGER NOT NULL,notes TEXT,created_at TEXT)",
                "CREATE TABLE practice_attempts(id INTEGER PRIMARY KEY,card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL,mode TEXT NOT NULL,correct INTEGER NOT NULL,answer TEXT NOT NULL,expected TEXT NOT NULL,practiced_at TEXT NOT NULL,day TEXT NOT NULL)",
                "CREATE TABLE quiz_mistakes(id INTEGER PRIMARY KEY,card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL,term TEXT NOT NULL UNIQUE,definition TEXT NOT NULL,wrong_count INTEGER,last_mistake_at TEXT)",
                "CREATE TABLE custom_tables(id TEXT PRIMARY KEY,name TEXT NOT NULL,data TEXT NOT NULL,updated_at TEXT DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE custom_games(id TEXT PRIMARY KEY,name TEXT NOT NULL,data TEXT NOT NULL,updated_at TEXT DEFAULT CURRENT_TIMESTAMP)",
                "CREATE TABLE custom_game_runs(id INTEGER PRIMARY KEY,game_id TEXT NOT NULL,correct INTEGER NOT NULL,total INTEGER NOT NULL,duration_seconds REAL NOT NULL,played_at TEXT NOT NULL)",
                "CREATE TABLE sentence_memory(lang TEXT NOT NULL,term_key TEXT NOT NULL,position INTEGER NOT NULL,text TEXT NOT NULL,translations TEXT NOT NULL DEFAULT '{}',kind TEXT NOT NULL,source TEXT NOT NULL,url TEXT DEFAULT '',author TEXT DEFAULT '',license TEXT DEFAULT '',PRIMARY KEY(lang,term_key,position))",
                "CREATE TABLE sentence_fetches(lang TEXT NOT NULL,term_key TEXT NOT NULL,attempted REAL,status TEXT,error TEXT,PRIMARY KEY(lang,term_key))",
                "CREATE TABLE daily_challenges(day TEXT,filter_key TEXT,card_ids TEXT,PRIMARY KEY(day,filter_key))",
                "CREATE TABLE sync_items(entity TEXT NOT NULL,local_id INTEGER NOT NULL,uuid TEXT NOT NULL UNIQUE,baseline TEXT NOT NULL DEFAULT '{}',revision INTEGER NOT NULL DEFAULT 0,dirty INTEGER NOT NULL DEFAULT 1,deleted INTEGER NOT NULL DEFAULT 0,generation INTEGER NOT NULL DEFAULT 1,PRIMARY KEY(entity,local_id))"};
        for (String statement : sql)
            db.execSQL(statement);
    }
}
