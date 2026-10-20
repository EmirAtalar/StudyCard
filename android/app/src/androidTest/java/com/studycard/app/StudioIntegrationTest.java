package com.studycard.app;

import android.content.Context;
import android.test.AndroidTestCase;
import android.test.RenamingDelegatingContext;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import org.json.JSONObject;

/** Real Android SQLite and ZIP integration; each test uses an isolated database. */
public final class StudioIntegrationTest extends AndroidTestCase {
    private CardStore store;
    private Context isolated;
    @Override
    protected void setUp() throws Exception {
        super.setUp();
        isolated = new RenamingDelegatingContext(
                getContext(), "studio-test-" + System.nanoTime() + "-") {
            @Override
            public Context getApplicationContext() {
                return this;
            }
        };
        store = new CardStore(isolated);
    }
    @Override
    protected void tearDown() throws Exception {
        store.close();
        isolated.deleteDatabase("study-card.db");
        super.tearDown();
    }
    private String card(String deck) {
        JSONObject card = new JSONObject();
        CardStore.put(card, "term", "apple");
        CardStore.put(card, "definition", "elma");
        CardStore.put(card, "deck_uuid", deck);
        CardStore.put(card, "source_lang", "en");
        CardStore.put(card, "target_lang", "tr");
        CardStore.put(card, "status", "new");
        CardStore.put(card, "due_date", java.time.LocalDate.now().toString());
        CardStore.put(card, "created_at", java.time.LocalDateTime.now().toString());
        return store.save("card", null, card);
    }
    public void testCompleteNativeRestore() throws Exception {
        String deck = store.list("deck").get(0).optString("uuid"), id = card(deck);
        store.rate(id, 3);
        store.recordPractice(id, "writing", "wrong", "apple", false);
        store.recordTimer("timer", 300, "focus");
        JSONObject table = StudioData.table("Verbs", "verbs", 1, 4);
        StudioData.save(store, "table", table);
        store.configSet(StudioData.menuKey("table", table.optString("id")), "true");
        JSONObject backup = store.deviceBackup();
        store.delete(id);
        store.delete(table.optString("id"));
        store.restoreDeviceBackup(backup);
        assertNotNull(store.get(id));
        assertEquals(1, store.list("review").size());
        assertEquals(1, store.list("practice").size());
        assertEquals(1, store.list("timer").size());
        assertNotNull(store.get(table.optString("id")));
        assertTrue(store.flag(StudioData.menuKey("table", table.optString("id")), false));
    }
    public void testBadBackupLeavesDataIntact() throws Exception {
        String id = card(store.list("deck").get(0).optString("uuid"));
        JSONObject backup = store.deviceBackup();
        JSONObject row = new JSONObject();
        CardStore.put(row, "key", "speech_volume");
        CardStore.put(row, "value", "999");
        backup.getJSONObject("tables").getJSONArray("config").put(row);
        try {
            store.restoreDeviceBackup(backup);
            fail("Out-of-range preferences should be rejected");
        } catch (IllegalArgumentException expected) {
        }
        assertNotNull(store.get(id));
    }
    public void testDesktopZipRoundTrip() throws Exception {
        String deck = store.list("deck").get(0).optString("uuid"), id = card(deck);
        store.rate(id, 3);
        store.recordPractice(id, "typing", "elma", "elma", true);
        store.recordTimer("timer", 1500, "session");
        store.rememberSentence("apple", "en", "I always pack an apple before leaving for work.",
                "tr", "İşe gitmeden önce her zaman bir elma alırım.");
        JSONObject table = StudioData.table("My table", "blank", 2, 2);
        StudioData.save(store, "table", table);
        JSONObject game = StudioData.game();
        CardStore.put(game, "name", "Listen");
        CardStore.put(game, "source", "library");
        CardStore.put(game, "source_id", deck);
        CardStore.put(game, "mode", "audio_dictation");
        StudioData.save(store, "game", game);
        store.recordGame(game.optString("id"), 1, 1, 2000);
        store.configSet(StudioData.menuKey("game", game.optString("id")), "true");
        ByteArrayOutputStream output = new ByteArrayOutputStream();
        DesktopBackup.write(isolated, store, output);
        JSONObject converted =
                DesktopBackup.read(isolated, new ByteArrayInputStream(output.toByteArray()));
        store.validateDeviceBackup(converted);
        store.restoreDeviceBackup(converted);
        assertNotNull(store.get(id));
        assertNotNull(store.get(deck));
        assertEquals(1, store.list("review").size());
        assertEquals(1, store.list("practice").size());
        assertEquals(1, store.list("timer").size());
        assertEquals(1, store.list("sentence").size());
        assertEquals(1, store.list("game_run").size());
        assertEquals(deck, store.get(game.optString("id")).optString("source_id"));
        assertTrue(store.flag(StudioData.menuKey("game", game.optString("id")), false));
        assertEquals("apple",
                StudioData.questions(store, store.get(game.optString("id"))).get(0).prompt);
    }
    public void testRenameKeepsGameColumnLinks() throws Exception {
        JSONObject table = StudioData.table("Source", "blank", 2, 2);
        String prompt = table.getJSONArray("columns").getJSONObject(0).getString("id"),
               answer = table.getJSONArray("columns").getJSONObject(1).getString("id");
        for (int i = 0; i < 2; i++) {
            JSONObject cells = table.getJSONArray("rows").getJSONObject(i).getJSONObject("cells");
            cells.put(prompt, i == 0 ? "apple" : "book");
            cells.put(answer, i == 0 ? "elma" : "kitap");
        }
        StudioData.save(store, "table", table);
        JSONObject game = StudioData.game();
        game.put("name", "Quiz");
        game.put("source", "table");
        game.put("source_id", table.getString("id"));
        game.put("prompt_column", prompt);
        game.put("answer_column", answer);
        table.getJSONArray("columns").getJSONObject(0).put("name", "Renamed");
        StudioData.save(store, "table", table);
        assertEquals(2, StudioData.questions(store, game).size());
    }
    public void testNativeRecoveryDoesNotExportCredentials() throws Exception {
        store.configSet("google_token", "private");
        store.configSet("account_token", "private");
        store.configSet("profile_name", "Ada");
        JSONObject backup = store.deviceBackup();
        String config = backup.getJSONObject("tables").getJSONArray("config").toString();
        assertFalse(config.contains("google_token"));
        assertFalse(config.contains("account_token"));
        assertTrue(config.contains("Ada"));
    }
}
