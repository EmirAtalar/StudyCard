package com.studycard.app;

import android.graphics.Color;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Supplier;
import org.json.JSONObject;

/** Settings, statistics, timer, sentence memory and card-based practice tools. */
final class MobileExtras {
    final MainActivity a;
    final StudioUi ui;
    final Map<String, Supplier<String>> controls = new LinkedHashMap<>();
    final List<LinearLayout> settingsCards = new ArrayList<>();
    final Map<LinearLayout, String> searchLabels = new LinkedHashMap<>();
    TextView timerLabel;
    String sentenceSearch = "";
    int memoryGeneration;
    final Runnable timerTick = new Runnable() {
        public void run() {
            refreshTimer();
            if (a.resumed && a.page == 14)
                a.handler.postDelayed(this, 200);
        }
    };
    MobileExtras(MainActivity activity) {
        a = activity;
        ui = new StudioUi(a);
    }
    void sound(boolean correct) {
        if (!a.store.flag("sfx_enabled", true))
            return;
        ToneGenerator tone = new ToneGenerator(AudioManager.STREAM_MUSIC,
                Math.max(0, Math.min(100, a.store.number("sfx_volume", 80))));
        tone.startTone(correct ? ToneGenerator.TONE_PROP_ACK : ToneGenerator.TONE_PROP_NACK, 120);
        a.handler.postDelayed(tone::release, 200);
    }
    LinearLayout settingsGroup(String title) {
        LinearLayout card = a.panel();
        card.addView(a.text(a.t(title), 20, a.INK));
        a.content.addView(card);
        settingsCards.add(card);
        searchLabels.put(card, a.t(title));
        return card;
    }
    void tag(LinearLayout card, String label) {
        searchLabels.put(card, searchLabels.get(card) + " " + a.t(label));
    }
    void settingText(LinearLayout card, String key, String label, String fallback) {
        tag(card, label);
        EditText input = a.field(card, a.t(label), a.store.config(key, fallback), false);
        controls.put(key, () -> input.getText().toString().trim());
    }
    void settingBool(LinearLayout card, String key, String label, boolean fallback) {
        tag(card, label);
        CheckBox input = a.check(card, label, a.store.flag(key, fallback));
        controls.put(key, () -> Boolean.toString(input.isChecked()));
    }
    void settingChoice(LinearLayout card, String key, String label, String[] labels,
            String[] values, String fallback) {
        tag(card, label);
        Spinner input = ui.options(card, label, labels, values, a.store.config(key, fallback));
        controls.put(key, () -> values[input.getSelectedItemPosition()]);
    }
    void settingInt(LinearLayout card, String key, String label, int fallback, int low, int high) {
        tag(card, label);
        EditText input = ui.number(card, label, a.store.number(key, fallback));
        controls.put(key, () -> Integer.toString(ui.number(input, low, high)));
    }
    void settings() {
        controls.clear();
        settingsCards.clear();
        searchLabels.clear();
        a.title(a.t("Settings"));
        a.hint(a.t("Make Studycard feel like your own learning space."));
        EditText search = a.field(a.content, a.t("Search settings"), "", false);
        LinearLayout appearance = settingsGroup("Appearance and profile");
        settingText(appearance, "profile_name", "Display name", "");
        settingChoice(appearance, "ui_language", "Language",
                new String[] {a.languageName("tr"), a.languageName("en"), a.languageName("de"),
                        a.languageName("es")},
                new String[] {"tr", "en", "de", "es"}, "tr");
        settingChoice(appearance, "theme", "Color theme",
                new String[] {"Slate", "Midnight blue", "Graphite"},
                new String[] {"dark_slate", "midnight", "graphite"}, "dark_slate");
        settingChoice(appearance, "accent_color", "Accent color",
                new String[] {"Emerald", "Blue", "Violet", "Amber", "Coral"},
                new String[] {"#10b981", "#38bdf8", "#a78bfa", "#fbbf24", "#fb7185"}, "#10b981");
        settingInt(appearance, "text_scale", "Text size (%)", 100, 90, 130);
        settingBool(appearance, "reduced_motion", "Reduce animations", false);
        settingBool(appearance, "show_phonetics", "Show pronunciation text", true);
        settingBool(appearance, "show_card_notes", "Show card notes", true);
        LinearLayout study = settingsGroup("Learning preferences");
        settingInt(study, "daily_goal", "Daily goal", 10, 5, 100);
        settingInt(study, "focus_goal_hours", "Focus goal (hours)", 1000, 1, 50000);
        settingInt(study, "session_size", "Cards per session", 50, 5, 200);
        settingBool(study, "shuffle_cards", "Shuffle study cards", true);
        settingBool(study, "practice_auto_next", "Advance after correct answers", true);
        settingInt(study, "practice_advance_ms", "Answer feedback duration (ms)", 300, 300, 5000);
        settingBool(study, "practice_autoplay", "Autoplay in listening and imitation", true);
        settingBool(study, "auto_pronounce", "Automatic pronunciation", false);
        settingChoice(study, "pronounce_trigger", "When to pronounce",
                new String[] {"Card appears", "Card flips", "Both"},
                new String[] {"appear", "flip", "both"}, "flip");
        LinearLayout speech = settingsGroup("Speech preferences");
        settingChoice(speech, "speech_speed", "Speech speed",
                new String[] {"0.5×", "0.75×", "1×", "1.25×", "1.5×", "1.75×", "2×"},
                new String[] {"0.5", "0.75", "1.0", "1.25", "1.5", "1.75", "2.0"}, "1.0");
        settingInt(speech, "speech_volume", "Speech volume (%)", 100, 0, 100);
        settingBool(speech, "audio_prefetch", "Prepare upcoming audio", true);
        settingBool(speech, "sfx_enabled", "Sound effects", true);
        settingInt(speech, "sfx_volume", "Sound effects volume (%)", 80, 0, 100);
        LinearLayout mobile = settingsGroup("Mobile and reminders");
        settingChoice(mobile, "startup_page", "Opening page",
                new String[] {"Study", "Library", "Create extension", "Statistics",
                        "Import / export", "Settings"},
                new String[] {"study", "library", "tables", "stats", "import", "settings"},
                "study");
        settingBool(mobile, "keep_screen_on", "Keep screen awake while learning", false);
        settingBool(mobile, "daily_notification_enabled", "Daily study reminder", false);
        settingText(mobile, "notification_time", "Reminder time (HH:mm)", "20:00");
        mobile.addView(
                a.text(a.t("Add the Studycard widget from your phone's home screen widget menu."),
                        14, a.MUTED));
        mobile.addView(a.button(a.t("Voice settings"), false, () -> {
            try {
                a.startActivity(new android.content.Intent("com.android.settings.TTS_SETTINGS"));
            } catch (android.content.ActivityNotFoundException missing) {
                a.startActivity(new android.content.Intent("android.settings.SETTINGS"));
            }
        }));
        search.addTextChangedListener(MobileStudio.watch(() -> {
            String needle = search.getText().toString().toLowerCase(java.util.Locale.ROOT);
            for (LinearLayout card : settingsCards)
                card.setVisibility(
                        searchLabels.get(card).toLowerCase(java.util.Locale.ROOT).contains(needle)
                                ? View.VISIBLE
                                : View.GONE);
        }));
        Button save = a.button(a.t("Save settings"), false, () -> {
            try {
                Map<String, String> values = new LinkedHashMap<>();
                for (Map.Entry<String, Supplier<String>> entry : controls.entrySet())
                    values.put(entry.getKey(), entry.getValue().get());
                String time = values.get("notification_time");
                if (time == null || !time.matches("([01][0-9]|2[0-3]):[0-5][0-9]")) {
                    a.toast("Use a valid time, for example 20:00.");
                    return;
                }
                if (values.get("profile_name").length() > 40) {
                    a.toast("Display names can contain up to 40 characters.");
                    return;
                }
                a.store.configUpdate(values);
                a.applyPreferences();
                MobileReminders.schedule(a, a.store);
                if (a.store.flag("daily_notification_enabled", false))
                    a.requestNotifications();
                StudyWidget.refresh(a);
                a.toast("Settings saved");
                a.buildRoot();
                a.render();
            } catch (IllegalArgumentException invalid) {
                a.toast(invalid.getMessage());
            }
        });
        save.setBackground(a.background(Color.rgb(21, 59, 54), 12));
        save.setTextColor(Color.rgb(110, 231, 183));
        a.icon(save, "check");
        a.content.addView(save);
        a.backupButtons();
        a.addButton(a.t("Import / export"), false, () -> a.navigate(5));
        a.addButton(a.t("Extensions"), false, () -> a.navigate(6));
        a.addButton(a.t("Statistics"), false, () -> a.navigate(13));
        a.addButton(a.t("Timer"), false, () -> a.navigate(14));
    }
    void statistics() {
        a.title(a.t("Statistics"));
        List<JSONObject> cards = a.store.list("card"), reviews = a.store.list("review"),
                         practices = a.store.list("practice"), runs = a.store.list("game_run");
        int mastered = 0, learning = 0, due = 0, favorites = 0, correct = 0;
        for (JSONObject card : cards) {
            if (card.optString("status").equals("mastered"))
                mastered++;
            if (card.optString("status").equals("learning"))
                learning++;
            if (a.due(card))
                due++;
            if (card.optInt("is_favorite") == 1)
                favorites++;
        }
        for (JSONObject attempt : practices) correct += attempt.optInt("correct");
        metric("Total words", cards.size());
        metric("Mastered", mastered);
        metric("Learning", learning);
        metric("Due reviews", due);
        metric("Favorites", favorites);
        metric("Review history", reviews.size());
        metric("Practice accuracy",
                practices.isEmpty() ? "—" : (Math.round(100. * correct / practices.size()) + "%"));
        metric("Games played", runs.size());
        long seconds = 0;
        for (JSONObject timer : a.store.list("timer")) seconds += timer.optLong("duration_seconds");
        metric("Focus time", formatDuration(seconds));
        a.content.addView(a.text(a.t("Last 7 days"), 22, a.INK));
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (int i = 6; i >= 0; i--) counts.put(LocalDate.now().minusDays(i).toString(), 0);
        for (JSONObject review : reviews) {
            String day = review.optString("reviewed_at");
            if (day.length() >= 10)
                day = day.substring(0, 10);
            if (counts.containsKey(day))
                counts.put(day, counts.get(day) + 1);
        }
        int max = 1;
        for (int count : counts.values()) max = Math.max(max, count);
        for (Map.Entry<String, Integer> entry : counts.entrySet()) {
            LinearLayout row = a.panel();
            row.addView(a.text(entry.getKey() + " · " + entry.getValue(), 14, a.MUTED));
            ProgressBar bar = new ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal);
            bar.setProgressTintList(android.content.res.ColorStateList.valueOf(a.GREEN));
            bar.setMax(max);
            bar.setProgress(entry.getValue());
            row.addView(bar);
            a.content.addView(row);
        }
        Set<String> activeDays = new HashSet<>();
        for (JSONObject review : reviews) {
            String day = review.optString("reviewed_at");
            if (day.length() >= 10)
                activeDays.add(day.substring(0, 10));
        }
        int streak = 0;
        LocalDate day = LocalDate.now();
        if (!activeDays.contains(day.toString()))
            day = day.minusDays(1);
        while (activeDays.contains(day.toString())) {
            streak++;
            day = day.minusDays(1);
        }
        metric("Study streak", a.t("{days} days", "days", streak));
        for (JSONObject game : a.store.list("game")) {
            int plays = 0, best = 0;
            for (JSONObject run : runs)
                if (game.optString("id").equals(run.optString("game_id"))) {
                    plays++;
                    if (run.optInt("total") > 0)
                        best = Math.max(best,
                                (int) Math.round(
                                        100. * run.optInt("correct") / run.optInt("total")));
                }
            LinearLayout card = a.panel();
            card.addView(a.text(game.optString("name"), 20, a.INK));
            card.addView(a.text(a.t("{plays} plays · Best: {best}%", "plays", plays, "best", best),
                    14, a.GREEN));
            a.content.addView(card);
        }
    }
    void metric(String title, Object value) {
        LinearLayout card = a.panel();
        card.addView(a.text(a.t(title), 14, a.MUTED));
        card.addView(a.text(String.valueOf(value), 25, a.GREEN));
        a.content.addView(card);
    }
    static String formatDuration(long seconds) {
        long minutes = seconds / 60;
        return String.format(
                java.util.Locale.ROOT, "%02d:%02d:%02d", minutes / 60, minutes % 60, seconds % 60);
    }
    long timerSeconds() {
        return a.store.timerElapsed();
    }
    void timer() {
        a.title(a.t("Timer"));
        a.hint(a.t("Focus countdown, Pomodoro and stopwatch. Sessions appear in statistics."));
        String[] modes = {"timer", "stopwatch"};
        Spinner mode = ui.options(a.content, "Mode", new String[] {"Focus timer", "Stopwatch"},
                modes, a.store.config("timer_mode", "timer"));
        mode.setEnabled(!a.store.flag("timer_running", false) && timerSeconds() == 0);
        a.selection(mode, pos -> {
            a.store.configSet("timer_mode", modes[pos]);
            a.render();
        });
        long totalFocus = 0;
        for (JSONObject run : a.store.list("timer")) totalFocus += run.optLong("duration_seconds");
        int goal = a.store.number("focus_goal_hours", 1000);
        a.hint(a.t("Focus goal: {hours}/{goal} hours", "hours",
                String.format(java.util.Locale.ROOT, "%.1f", totalFocus / 3600.), "goal", goal));
        ProgressBar progress = new ProgressBar(a, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(Math.max(1, goal * 60));
        progress.setProgress((int) Math.min(Integer.MAX_VALUE, totalFocus / 60));
        progress.setProgressTintList(android.content.res.ColorStateList.valueOf(a.GREEN));
        a.content.addView(progress);
        timerLabel = a.text("", 42, a.GREEN);
        timerLabel.setGravity(android.view.Gravity.CENTER);
        a.content.addView(timerLabel);
        refreshTimer();
        if (!a.store.config("timer_mode", "timer").equals("stopwatch")) {
            EditText duration = ui.number(
                    a.content, "Focus minutes", a.store.number("timer_duration", 1500) / 60);
            duration.setEnabled(!a.store.flag("timer_running", false) && timerSeconds() == 0);
            a.addButton(a.t("Apply duration"), false, () -> {
                try {
                    a.store.configSet(
                            "timer_duration", Integer.toString(ui.number(duration, 1, 600) * 60));
                    a.render();
                } catch (IllegalArgumentException invalid) {
                    a.toast(invalid.getMessage());
                }
            });
            LinearLayout presets = a.row();
            for (int minutes : new int[] {5, 25, 50}) {
                Button preset = a.button(minutes + " " + a.t("min"), false, () -> {
                    stopTimer(false);
                    a.store.configSet("timer_duration", Integer.toString(minutes * 60));
                    a.render();
                });
                presets.addView(preset, new LinearLayout.LayoutParams(0, a.dp(50), 1));
            }
            a.content.addView(presets);
        }
        EditText notes =
                a.field(a.content, a.t("Session notes"), a.store.config("timer_notes", ""), true);
        notes.addTextChangedListener(MobileStudio.watch(
                () -> a.store.configSet("timer_notes", notes.getText().toString())));
        a.addButton(a.t(a.store.flag("timer_running", false) ? "Pause" : "Start / resume"), true,
                () -> {
                    if (a.store.flag("timer_running", false)) {
                        a.store.configSet("timer_elapsed", Long.toString(timerSeconds()));
                        a.store.configSet("timer_running", "false");
                        MobileReminders.cancelTimer(a);
                    } else {
                        a.store.configSet(
                                "timer_started", Long.toString(System.currentTimeMillis()));
                        a.store.configSet("timer_running", "true");
                        MobileReminders.scheduleTimer(a, a.store);
                        a.requestNotifications();
                    }
                    a.render();
                });
        a.addButton(a.t("Finish and save session"), false, () -> {
            stopTimer(true);
            a.render();
        });
        a.addButton(a.t("Reset"), false, () -> {
            stopTimer(false);
            a.render();
        });
        for (JSONObject run :
                a.store.list("timer").subList(0, Math.min(10, a.store.list("timer").size()))) {
            LinearLayout card = a.panel();
            card.addView(a.text(run.optString("created_at").replace('T', ' '), 13, a.MUTED));
            card.addView(a.text(formatDuration(run.optLong("duration_seconds")) + " · "
                            + a.t(run.optString("mode").equals("timer") ? "Focus timer"
                                                                        : "Stopwatch"),
                    20, a.INK));
            if (!run.optString("notes").isEmpty())
                card.addView(a.text(run.optString("notes"), 15, a.MUTED));
            a.content.addView(card);
        }
        a.handler.removeCallbacks(timerTick);
        if (a.resumed)
            a.handler.post(timerTick);
    }
    void refreshTimer() {
        if (a.store.config("timer_mode", "timer").equals("timer")
                && a.store.flag("timer_running", false)
                && timerSeconds() >= a.store.number("timer_duration", 1500)) {
            stopTimer(true);
            if (a.page == 14)
                a.render();
            a.toast("Focus session complete!");
            return;
        }
        long seconds = a.store.config("timer_mode", "timer").equals("timer")
                ? Math.max(0, a.store.number("timer_duration", 1500) - timerSeconds())
                : timerSeconds();
        if (timerLabel != null)
            timerLabel.setText(formatDuration(seconds));
    }
    void stopTimer(boolean save) {
        a.store.finishTimer(save);
        MobileReminders.cancelTimer(a);
        StudyWidget.refresh(a);
    }
    void beginLibraryGame(String mode, List<JSONObject> cards) {
        JSONObject game = StudioData.game();
        CardStore.put(game, "name", a.t(mode.equals("matching") ? "Speed Match" : "Practice Quiz"));
        CardStore.put(game, "mode", mode);
        CardStore.put(game, "question_count",
                mode.equals("matching") ? 8 : Math.min(100, a.store.number("session_size", 50)));
        JSONArrayBuilder.fill(game, cards);
        a.studio.startGame(game, false);
    }
    static final class JSONArrayBuilder {
        static void fill(JSONObject game, List<JSONObject> cards) {
            org.json.JSONArray pairs = new org.json.JSONArray();
            for (JSONObject card : cards) {
                JSONObject pair = new JSONObject();
                CardStore.put(pair, "prompt", card.optString("term"));
                CardStore.put(pair, "answer", card.optString("definition"));
                CardStore.put(pair, "card_id", card.optString("uuid"));
                CardStore.put(pair, "language",
                        CardTransfer.language(card.optString("source_lang", "en")));
                CardStore.put(pair, "answer_language",
                        CardTransfer.language(card.optString("target_lang", "tr")));
                pairs.put(pair);
            }
            CardStore.put(game, "manual_pairs", pairs);
            if (!cards.isEmpty()) {
                CardStore.put(game, "language",
                        CardTransfer.language(cards.get(0).optString("source_lang", "en")));
                CardStore.put(game, "answer_language",
                        CardTransfer.language(cards.get(0).optString("target_lang", "tr")));
            }
        }
    }
    List<JSONObject> filtered(String kind) {
        List<JSONObject> result = new ArrayList<>();
        Set<String> mistakes = new HashSet<>();
        if (kind.equals("mistakes"))
            for (JSONObject mistake : a.store.list("mistake"))
                mistakes.add(mistake.optString("card_uuid"));
        if (kind.equals("mistakes"))
            for (JSONObject attempt : a.store.list("practice"))
                if (attempt.optInt("correct") == 0 && !attempt.optBoolean("mistake_cleared"))
                    mistakes.add(attempt.optString("card_uuid"));
        for (JSONObject card : a.store.list("card"))
            if (kind.equals("favorites") ? card.optInt("is_favorite") == 1
                                         : mistakes.contains(card.optString("uuid")))
                result.add(card);
        return result;
    }
    void filteredCards(String kind) {
        a.title(a.t(kind.equals("favorites") ? "Favorites" : "My Mistakes"));
        List<JSONObject> cards = filtered(kind);
        a.hint(a.t("{count} words", "count", cards.size()));
        a.addButton(a.t("Written Recall"), true, () -> a.beginPractice("writing", cards));
        a.addButton(a.t("Practice Quiz"), false, () -> beginLibraryGame("quiz", cards));
        if (kind.equals("mistakes"))
            a.addButton(a.t("Clear mistake history"), false,
                    ()
                            -> ui.confirm("Clear mistake history",
                                    a.t("The mistakes list will be cleared. Your cards and practice statistics are kept."),
                                    "Clear", () -> {
                                        a.store.clearMistakes();
                                        a.render();
                                    }));
        for (JSONObject card : cards) {
            LinearLayout panel = a.panel();
            panel.addView(a.text(card.optString("term"), 22, a.INK));
            panel.addView(a.text(card.optString("definition"), 17, a.GREEN));
            panel.addView(a.button(a.t("Listen"), false, () -> a.speak(card)));
            panel.addView(a.button(a.t("Edit"), false, () -> a.edit(card)));
            a.content.addView(panel);
        }
    }
    void dailyChallenge() {
        String day = LocalDate.now().toString();
        List<JSONObject> cards = a.store.list("card");
        if (cards.size() < 2) {
            a.toast("This game needs at least two different answers.");
            return;
        }
        JSONObject saved = null;
        for (JSONObject challenge : a.store.list("challenge"))
            if (day.equals(challenge.optString("day"))
                    && challenge.optString("filter_key").isEmpty()) {
                saved = challenge;
                break;
            }
        List<JSONObject> selected = new ArrayList<>();
        if (saved != null) {
            org.json.JSONArray ids = saved.optJSONArray("card_ids");
            for (int i = 0; i < ids.length(); i++) {
                JSONObject card = a.store.get(ids.optString(i));
                if (card != null)
                    selected.add(card);
            }
        } else {
            cards.sort((left, right) -> left.optString("uuid").compareTo(right.optString("uuid")));
            java.util.Collections.shuffle(cards, new java.util.Random(day.hashCode()));
            selected.addAll(cards.subList(0, Math.min(10, cards.size())));
            saved = new JSONObject();
            CardStore.put(saved, "day", day);
            CardStore.put(saved, "filter_key", "");
            org.json.JSONArray ids = new org.json.JSONArray();
            for (JSONObject card : selected) ids.put(card.optString("uuid"));
            CardStore.put(saved, "card_ids", ids);
            a.store.save("challenge", null, saved);
        }
        JSONObject game = StudioData.game();
        CardStore.put(game, "name", a.t("Daily challenge"));
        CardStore.put(game, "mode", "quiz");
        CardStore.put(game, "practice_mode", "challenge");
        CardStore.put(game, "question_count", 10);
        JSONArrayBuilder.fill(game, selected);
        a.studio.startGame(game, false);
    }
    void sentenceMemory() {
        a.title(a.t("Sentence Memory"));
        a.hint(a.t("Search full usage examples, save a translation and practice aloud."));
        EditText search = a.field(a.content, a.t("Search word or sentence"), sentenceSearch, false);
        List<JSONObject> cards = a.store.list("card");
        LinearLayout results = a.column();
        a.content.addView(results);
        List<JSONObject> prepared = new ArrayList<>();
        results.addView(a.text(a.t("Preparing practice…"), 15, a.MUTED));
        Runnable fill = () -> {
            results.removeAllViews();
            String needle = sentenceSearch.toLowerCase(java.util.Locale.ROOT);
            int count = 0;
            for (JSONObject card : prepared) {
                String sentence = card.optString("memory_sentence");
                if (!(card.optString("term") + " " + sentence)
                                .toLowerCase(java.util.Locale.ROOT)
                                .contains(needle))
                    continue;
                if (count++ >= 50)
                    continue;
                LinearLayout panel = a.panel();
                panel.addView(a.text(card.optString("term"), 21, a.GREEN));
                panel.addView(a.text(sentence, 18, a.INK));
                String translation = sentence.equals(card.optString("example_sentence"))
                        ? card.optString("example_translation")
                        : SentenceExamples.translation(a, sentence,
                                  CardTransfer.language(card.optString("target_lang", "tr")));
                if (!translation.isEmpty())
                    panel.addView(a.text(translation, 15, a.MUTED));
                panel.addView(a.button(a.t("Listen"), false,
                        ()
                                -> a.speech.play(sentence,
                                        CardTransfer.language(card.optString("source_lang", "en")),
                                        a::toast)));
                panel.addView(a.button(a.t("Edit card"), false, () -> a.edit(card)));
                results.addView(panel);
            }
            if (count == 0)
                results.addView(a.text(
                        a.t("No contextual examples yet. Add a full usage sentence or connect to search."),
                        15, a.MUTED));
        };
        int ticket = ++memoryGeneration;
        a.worker.execute(() -> {
            List<JSONObject> ready = new ArrayList<>();
            for (JSONObject card : cards) {
                if (ticket != memoryGeneration || Thread.currentThread().isInterrupted())
                    return;
                String sentence = a.usageSentence(card);
                if (sentence.isEmpty())
                    continue;
                CardStore.put(card, "memory_sentence", sentence);
                ready.add(card);
            }
            a.handler.post(() -> {
                if (ticket != memoryGeneration || a.page != 15 || a.isDestroyed())
                    return;
                prepared.addAll(ready);
                fill.run();
            });
        });
        search.addTextChangedListener(MobileStudio.watch(() -> {
            sentenceSearch = search.getText().toString();
            fill.run();
        }));
        a.addButton(a.t("Shadowing"), true, () -> a.beginPractice("shadowing", cards));
        a.addButton(a.t("Fill in the Blank"), false, () -> a.beginPractice("cloze", cards));
    }
}
