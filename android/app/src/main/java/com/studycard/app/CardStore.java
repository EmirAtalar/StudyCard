package com.studycard.app;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** Durable offline library/outbox. Network I/O never runs in a SQLite transaction. */
public final class CardStore extends SQLiteOpenHelper implements java.io.Closeable {
    public CardStore(Context context) {
        super(context.getApplicationContext(), "study-card.db", null, 1);
        getWritableDatabase();
        if (config("initialized", "").isEmpty()) {
            createDeck("Kelimelerim", "Telefondaki kelimelerim");
            configSet("initialized", "1");
        }
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL(
                "CREATE TABLE items(entity TEXT NOT NULL, uuid TEXT PRIMARY KEY, data TEXT NOT NULL, baseline TEXT NOT NULL DEFAULT '{}', dirty INTEGER NOT NULL DEFAULT 1, deleted INTEGER NOT NULL DEFAULT 0, generation INTEGER NOT NULL DEFAULT 1, revision INTEGER NOT NULL DEFAULT 0)");
        db.execSQL("CREATE TABLE config(key TEXT PRIMARY KEY,value TEXT NOT NULL)");
        db.execSQL(
                "CREATE TABLE recovery(id INTEGER PRIMARY KEY AUTOINCREMENT,uuid TEXT,entity TEXT,data TEXT,saved_at TEXT)");
    }
    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {}

    static JSONObject json(String value) {
        try {
            return new JSONObject(value);
        } catch (JSONException e) {
            throw new IllegalStateException("Kütüphane verisi okunamadı", e);
        }
    }
    static void put(JSONObject obj, String key, Object value) {
        try {
            obj.put(key, value == null ? JSONObject.NULL : value);
        } catch (JSONException e) {
            throw new IllegalArgumentException(e);
        }
    }
    static String uuid() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    public synchronized String config(String key, String fallback) {
        try (Cursor c = getReadableDatabase().rawQuery(
                     "SELECT value FROM config WHERE key=?", new String[] {key})) {
            return c.moveToFirst() ? c.getString(0) : fallback;
        }
    }
    public synchronized void configSet(String key, String value) {
        ContentValues v = new ContentValues();
        v.put("key", key);
        v.put("value", value);
        getWritableDatabase().insertWithOnConflict(
                "config", null, v, SQLiteDatabase.CONFLICT_REPLACE);
    }

    boolean flag(String key, boolean fallback) {
        return config(key, fallback ? "true" : "false").equals("true");
    }
    int number(String key, int fallback) {
        try {
            return Integer.parseInt(config(key, Integer.toString(fallback)));
        } catch (NumberFormatException invalid) {
            return fallback;
        }
    }
    float decimal(String key, float fallback) {
        try {
            float value = Float.parseFloat(config(key, Float.toString(fallback)));
            return Float.isFinite(value) ? value : fallback;
        } catch (NumberFormatException invalid) {
            return fallback;
        }
    }
    synchronized void configUpdate(Map<String, String> values) {
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            for (Map.Entry<String, String> entry : values.entrySet())
                configSet(entry.getKey(), entry.getValue());
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }
    synchronized String saveDocument(String entity, String id, JSONObject data) {
        JSONObject clean = json(data.toString());
        clean.remove("uuid");
        ContentValues values = new ContentValues();
        values.put("entity", entity);
        values.put("uuid", id);
        values.put("data", clean.toString());
        values.put("dirty", 1);
        getWritableDatabase().insertWithOnConflict(
                "items", null, values, SQLiteDatabase.CONFLICT_REPLACE);
        return id;
    }
    synchronized void recordPractice(
            String cardId, String mode, String answer, String expected, boolean correct) {
        JSONObject attempt = new JSONObject();
        put(attempt, "card_uuid", cardId);
        put(attempt, "mode", mode);
        put(attempt, "answer", answer);
        put(attempt, "expected", expected);
        put(attempt, "correct", correct ? 1 : 0);
        put(attempt, "day", LocalDate.now().toString());
        put(attempt, "practiced_at", LocalDateTime.now().toString());
        save("practice", null, attempt);
    }
    synchronized void clearMistakes() {
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            for (JSONObject attempt : list("practice"))
                if (attempt.optInt("correct") == 0) {
                    put(attempt, "mistake_cleared", true);
                    save("practice", attempt.optString("uuid"), attempt);
                }
            db.execSQL("UPDATE items SET deleted=1 WHERE entity='mistake'");
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }
    synchronized void recordGame(String gameId, int correct, int total, long millis) {
        JSONObject run = new JSONObject();
        put(run, "game_id", gameId);
        put(run, "correct", correct);
        put(run, "total", total);
        put(run, "duration_seconds", Math.max(0, millis) / 1000.);
        put(run, "played_at", LocalDateTime.now().toString());
        save("game_run", null, run);
    }
    static String sentencePrefix(String term, String language) {
        try {
            byte[] bytes = java.security.MessageDigest.getInstance("SHA-256").digest(
                    (language + "\u0001" + wordKey(term))
                            .getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder key = new StringBuilder("sentence-");
            for (byte value : bytes)
                key.append(String.format(java.util.Locale.ROOT, "%02x", value));
            return key + "-";
        } catch (java.security.NoSuchAlgorithmException impossible) {
            throw new IllegalStateException(impossible);
        }
    }
    synchronized void rememberSentence(
            String term, String language, String sentence, String target, String translation) {
        JSONObject value = new JSONObject();
        put(value, "lang", language);
        put(value, "term_key", wordKey(term));
        put(value, "text", sentence);
        JSONObject translated = new JSONObject();
        put(translated, target, translation);
        put(value, "translations", translated);
        put(value, "kind", "example");
        put(value, "source", "tatoeba");
        saveDocument("sentence", sentencePrefix(term, language) + uuidFor(sentence), value);
    }
    static String uuidFor(String value) {
        return UUID.nameUUIDFromBytes(value.getBytes(java.nio.charset.StandardCharsets.UTF_8))
                .toString()
                .replace("-", "");
    }
    synchronized List<JSONObject> sentences(String term, String language) {
        List<JSONObject> result = new ArrayList<>();
        try (Cursor c = getReadableDatabase().rawQuery(
                     "SELECT data FROM items WHERE entity='sentence' AND deleted=0 AND uuid LIKE ?",
                     new String[] {sentencePrefix(term, language) + "%"})) {
            while (c.moveToNext())
                result.add(json(c.getString(0)));
        }
        return result;
    }
    synchronized void recordTimer(String mode, long seconds, String notes) {
        if (seconds <= 0)
            return;
        JSONObject run = new JSONObject();
        put(run, "mode", mode);
        put(run, "duration_seconds", seconds);
        put(run, "notes", notes);
        put(run, "created_at", LocalDateTime.now().toString());
        save("timer", null, run);
    }
    synchronized long timerElapsed() {
        long elapsed = number("timer_elapsed", 0);
        if (flag("timer_running", false)) {
            try {
                elapsed += Math.max(0,
                        (System.currentTimeMillis() - Long.parseLong(config("timer_started", "0")))
                                / 1000);
            } catch (NumberFormatException ignored) {
            }
        }
        return elapsed;
    }
    synchronized void finishTimer(boolean save) {
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            long elapsed = timerElapsed();
            if (save && elapsed > 0)
                recordTimer(config("timer_mode", "timer"),
                        config("timer_mode", "timer").equals("timer")
                                ? Math.min(elapsed, number("timer_duration", 1500))
                                : elapsed,
                        config("timer_notes", ""));
            configSet("timer_running", "false");
            configSet("timer_elapsed", "0");
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }

    public synchronized JSONObject deviceBackup() {
        JSONObject backup = new JSONObject();
        put(backup, "format", "studycard-android-device-backup");
        put(backup, "version", 1);
        put(backup, "created_at", LocalDateTime.now().toString());
        JSONObject tables = new JSONObject();
        SQLiteDatabase database = getWritableDatabase();
        database.beginTransaction();
        try {
            for (String table : new String[] {"items", "config", "recovery"}) {
                JSONArray rows = new JSONArray();
                try (Cursor cursor = database.rawQuery("SELECT * FROM " + table, null)) {
                    while (cursor.moveToNext()) {
                        if (table.equals("config")) {
                            String key = cursor.getString(cursor.getColumnIndexOrThrow("key"));
                            if (key.contains("account") || key.contains("token")
                                    || key.startsWith("google_") || key.startsWith("firebase_")
                                    || key.startsWith("cloud_") || key.startsWith("sync")
                                    || key.equals("cursor") || key.equals("last_sync"))
                                continue;
                        }
                        JSONObject row = new JSONObject();
                        for (int i = 0; i < cursor.getColumnCount(); i++)
                            put(row, cursor.getColumnName(i),
                                    cursor.isNull(i) ? JSONObject.NULL
                                            : cursor.getType(i) == Cursor.FIELD_TYPE_INTEGER
                                            ? cursor.getLong(i)
                                            : cursor.getString(i));
                        rows.put(row);
                    }
                }
                put(tables, table, rows);
            }
            database.setTransactionSuccessful();
        } finally {
            database.endTransaction();
        }
        put(backup, "tables", tables);
        return backup;
    }

    public synchronized void validateDeviceBackup(JSONObject backup) throws JSONException {
        new BackupValidator().check(backup);
        if (!backup.getString("format").equals("studycard-android-device-backup")
                || backup.getInt("version") != 1)
            throw new JSONException("Unsupported backup format");
        JSONObject tables = backup.getJSONObject("tables");
        java.util.Set<String> ids = new java.util.HashSet<>();
        for (String table : new String[] {"items", "config", "recovery"}) {
            JSONArray rows = tables.getJSONArray(table);
            if (rows.length() > 200000)
                throw new JSONException("Backup is too large");
            for (int i = 0; i < rows.length(); i++) {
                JSONObject row = rows.getJSONObject(i);
                if (table.equals("items")) {
                    String id = row.getString("uuid"), entity = row.getString("entity");
                    JSONObject document = new JSONObject(row.getString("data"));
                    if (id.isEmpty() || !ids.add(id))
                        throw new JSONException("Invalid backup items");
                    if (entity.equals("table")) {
                        StudioData.validateTable(document);
                        if (!id.equals(document.optString("id")))
                            throw new JSONException("Invalid table identity");
                    }
                    if (entity.equals("game")) {
                        StudioData.validateGame(document);
                        if (!id.equals(document.optString("id")))
                            throw new JSONException("Invalid game identity");
                    }
                } else if (table.equals("config")) {
                    row.getString("key");
                    row.getString("value");
                }
            }
        }
    }

    public synchronized void restoreDeviceBackup(JSONObject backup) throws JSONException {
        validateDeviceBackup(backup);
        JSONObject tables = backup.getJSONObject("tables");
        SQLiteDatabase database = getWritableDatabase();
        database.beginTransaction();
        try {
            for (String table : new String[] {"items", "config", "recovery"}) {
                java.util.Set<String> columns = new java.util.HashSet<>();
                try (Cursor cursor = database.rawQuery("PRAGMA table_info(" + table + ")", null)) {
                    while (cursor.moveToNext())
                        columns.add(cursor.getString(1));
                }
                database.delete(table, null, null);
                JSONArray rows = tables.getJSONArray(table);
                for (int i = 0; i < rows.length(); i++) {
                    JSONObject row = rows.getJSONObject(i);
                    ContentValues values = new ContentValues();
                    for (java.util.Iterator<String> keys = row.keys(); keys.hasNext();) {
                        String key = keys.next();
                        if (!columns.contains(key))
                            continue;
                        Object value = row.get(key);
                        if (value == JSONObject.NULL)
                            values.putNull(key);
                        else if (value instanceof Number)
                            values.put(key, ((Number) value).longValue());
                        else
                            values.put(key, value.toString());
                    }
                    database.insertOrThrow(table, null, values);
                }
            }
            database.setTransactionSuccessful();
        } finally {
            database.endTransaction();
        }
    }

    public synchronized List<JSONObject> list(String entity) {
        List<JSONObject> result = new ArrayList<>();
        try (Cursor c = getReadableDatabase().rawQuery(
                     "SELECT uuid,data FROM items WHERE entity=? AND deleted=0 ORDER BY rowid DESC",
                     new String[] {entity})) {
            while (c.moveToNext()) {
                JSONObject data = json(c.getString(1));
                put(data, "uuid", c.getString(0));
                result.add(data);
            }
        }
        return result;
    }

    static String wordKey(String word) {
        return java.text.Normalizer.normalize(word, java.text.Normalizer.Form.NFKC)
                .toLowerCase(java.util.Locale.ROOT)
                .replace("ß", "ss")
                .replace("\u0307", "")
                .trim()
                .replaceAll("\\s+", " ");
    }
    public synchronized List<JSONObject> duplicates(String word, String excluded) {
        List<JSONObject> found = new ArrayList<>();
        String key = wordKey(word);
        if (key.isEmpty())
            return found;
        for (JSONObject card : list("card"))
            if (!card.optString("uuid").equals(excluded)
                    && key.equals(wordKey(card.optString("term"))))
                found.add(card);
        return found;
    }

    public synchronized JSONObject get(String id) {
        try (Cursor c = getReadableDatabase().rawQuery(
                     "SELECT data FROM items WHERE uuid=? AND deleted=0", new String[] {id})) {
            if (!c.moveToFirst())
                return null;
            JSONObject result = json(c.getString(0));
            put(result, "uuid", id);
            return result;
        }
    }

    public synchronized String save(String entity, String id, JSONObject data) {
        JSONObject clean = json(data.toString());
        clean.remove("uuid");
        if (id == null || id.isEmpty()) {
            id = uuid();
            ContentValues v = new ContentValues();
            v.put("entity", entity);
            v.put("uuid", id);
            v.put("data", clean.toString());
            getWritableDatabase().insertOrThrow("items", null, v);
        } else {
            getWritableDatabase().execSQL(
                    "UPDATE items SET data=?,dirty=1,generation=generation+1 WHERE uuid=? AND deleted=0",
                    new Object[] {clean.toString(), id});
        }
        return id;
    }

    public synchronized String createDeck(String name, String description) {
        JSONObject data = new JSONObject();
        put(data, "name", name.trim());
        put(data, "description", description.trim());
        put(data, "icon", "");
        put(data, "color", "#10b981");
        put(data, "created_at", LocalDateTime.now().toString());
        return save("deck", null, data);
    }

    public synchronized void delete(String id) {
        JSONObject data = get(id);
        if (data == null)
            return;
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            boolean isDeck = false;
            try (Cursor c = db.rawQuery(
                         "SELECT entity FROM items WHERE uuid=?", new String[] {id})) {
                isDeck = c.moveToFirst() && c.getString(0).equals("deck");
            }
            if (isDeck) {
                for (JSONObject card : list("card"))
                    if (id.equals(card.optString("deck_uuid"))) {
                        db.execSQL(
                                "UPDATE items SET deleted=1,dirty=1,generation=generation+1 WHERE uuid=?",
                                new Object[] {card.optString("uuid")});
                    }
            }
            db.execSQL("UPDATE items SET deleted=1,dirty=1,generation=generation+1 WHERE uuid=?",
                    new Object[] {id});
            for (JSONObject run : list("game_run"))
                if (id.equals(run.optString("game_id")))
                    db.execSQL("UPDATE items SET deleted=1 WHERE uuid=?",
                            new Object[] {run.optString("uuid")});
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }

    public synchronized int pending() {
        try (Cursor c = getReadableDatabase().rawQuery(
                     "SELECT count(*) FROM items WHERE dirty=1", null)) {
            c.moveToFirst();
            return c.getInt(0);
        }
    }

    public synchronized void rate(String id, int rating) {
        JSONObject card = get(id);
        if (card == null)
            return;
        int reps = card.optInt("repetition_count", 0), interval = card.optInt("interval_days", 1);
        double ease = card.optDouble("ease_factor", 2.5);
        String status = "learning";
        LocalDate due;
        if (rating == 1) {
            reps = 0;
            interval = 1;
            due = LocalDate.now();
        } else if (rating == 2) {
            reps++;
            interval = Math.max(1, (int) (interval * 1.2));
            ease = Math.max(1.3, ease - .15);
            due = LocalDate.now().plusDays(interval);
        } else {
            reps++;
            interval = reps == 1 ? 1
                    : reps == 2  ? 3
                                 : Math.max((int) (interval * ease), interval + 1);
            ease += .1;
            if (reps >= 3 || interval >= 7)
                status = "mastered";
            due = LocalDate.now().plusDays(interval);
        }
        put(card, "repetition_count", reps);
        put(card, "interval_days", interval);
        put(card, "ease_factor", ease);
        put(card, "status", status);
        put(card, "due_date", due.toString());
        put(card, "last_reviewed", LocalDateTime.now().toString());
        save("card", id, card);
        JSONObject log = new JSONObject();
        put(log, "card_uuid", id);
        put(log, "rating", rating);
        put(log, "reviewed_at", LocalDateTime.now().toString());
        save("review", null, log);
        String today = LocalDate.now().toString();
        int count = today.equals(config("review_day", ""))
                ? Integer.parseInt(config("review_count", "0"))
                : 0;
        configSet("review_day", today);
        configSet("review_count", Integer.toString(count + 1));
    }

    static JSONObject diff(JSONObject current, JSONObject baseline) {
        JSONObject patch = new JSONObject();
        Iterator<String> keys = current.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            Object v = current.opt(key), b = baseline.opt(key);
            if (!baseline.has(key) || !String.valueOf(v).equals(String.valueOf(b)))
                put(patch, key, v);
        }
        return patch;
    }

    public static final class Batch {
        final JSONArray changes = new JSONArray();
        final Map<String, JSONObject> sent = new LinkedHashMap<>();
    }

    public synchronized Batch batch() {
        Batch batch = new Batch();
        int size = 0;
        try (Cursor c = getReadableDatabase().rawQuery(
                     "SELECT entity,uuid,data,baseline,deleted,generation FROM items WHERE dirty=1 ORDER BY CASE entity WHEN 'deck' THEN 0 ELSE 1 END,rowid LIMIT 100",
                     null)) {
            while (c.moveToNext()) {
                JSONObject data = c.getInt(4) == 1 ? new JSONObject() : json(c.getString(2));
                JSONObject change = new JSONObject();
                put(change, "entity", c.getString(0));
                put(change, "uuid", c.getString(1));
                put(change, "deleted", c.getInt(4) == 1);
                put(change, "data", diff(data, json(c.getString(3))));
                size += change.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8).length;
                if (size > 1500000 && batch.changes.length() > 0)
                    break;
                batch.changes.put(change);
                JSONObject sent = new JSONObject();
                put(sent, "data", data);
                put(sent, "generation", c.getInt(5));
                batch.sent.put(c.getString(1), sent);
            }
        }
        return batch;
    }

    public synchronized void apply(Map<String, JSONObject> incoming, Batch batch, long cursor) {
        SQLiteDatabase db = getWritableDatabase();
        db.beginTransaction();
        try {
            // Parent records need to exist before children are displayed.
            List<JSONObject> records = new ArrayList<>(incoming.values());
            java.util.Collections.sort(records,
                    (a, b)
                            -> Integer.compare(a.optString("entity").equals("deck") ? 0 : 1,
                                    b.optString("entity").equals("deck") ? 0 : 1));
            for (JSONObject record : records) {
                String id = record.optString("uuid"), entity = record.optString("entity");
                JSONObject remote = record.optJSONObject("data");
                boolean exists = false, deleted = false, dirty = false;
                int generation = 1;
                JSONObject local = new JSONObject(), baseline = new JSONObject();
                try (Cursor c = db.rawQuery(
                             "SELECT data,baseline,dirty,deleted,generation FROM items WHERE uuid=?",
                             new String[] {id})) {
                    if (c.moveToFirst()) {
                        exists = true;
                        local = json(c.getString(0));
                        baseline = json(c.getString(1));
                        dirty = c.getInt(2) == 1;
                        deleted = c.getInt(3) == 1;
                        generation = c.getInt(4);
                    }
                }
                JSONObject sent = batch.sent.get(id);
                JSONObject reference = sent == null ? baseline : sent.optJSONObject("data");
                JSONObject pending = dirty && !deleted ? diff(local, reference) : new JSONObject();
                boolean dirtyDelete =
                        deleted && (sent == null || sent.optInt("generation") != generation);
                if (record.optBoolean("deleted") && exists && !deleted) {
                    ContentValues backup = new ContentValues();
                    backup.put("uuid", id);
                    backup.put("entity", entity);
                    backup.put("data", local.toString());
                    backup.put("saved_at", LocalDateTime.now().toString());
                    db.insertOrThrow("recovery", null, backup);
                }
                JSONObject merged = json(remote.toString());
                Iterator<String> keys = pending.keys();
                while (keys.hasNext()) {
                    String key = keys.next();
                    put(merged, key, pending.opt(key));
                }
                ContentValues values = new ContentValues();
                values.put("entity", entity);
                values.put("uuid", id);
                values.put("data", dirtyDelete ? local.toString() : merged.toString());
                values.put("baseline", remote.toString());
                values.put("revision", record.optLong("revision"));
                values.put("generation", generation);
                values.put("deleted", record.optBoolean("deleted") || dirtyDelete ? 1 : 0);
                values.put("dirty",
                        !record.optBoolean("deleted") && (dirtyDelete || pending.length() > 0) ? 1
                                                                                               : 0);
                db.insertWithOnConflict("items", null, values, SQLiteDatabase.CONFLICT_REPLACE);
            }
            configSet("cursor", Long.toString(cursor));
            configSet("last_sync", LocalDateTime.now().toString());
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
    }
}
