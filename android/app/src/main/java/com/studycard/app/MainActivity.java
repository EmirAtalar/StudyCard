package com.studycard.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.WindowInsets;
import android.view.inputmethod.InputMethodManager;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import org.json.JSONArray;
import org.json.JSONObject;

/** Android's native views, SQLite and speech engine; no webview or desktop runtime. */
public final class MainActivity extends Activity {
    int BG = Color.rgb(13, 18, 28), PANEL = Color.rgb(18, 24, 36);
    int GREEN = Color.rgb(16, 185, 129), INK = Color.rgb(241, 245, 249),
        MUTED = Color.rgb(148, 163, 184);
    L10n locale;
    String uiLanguage;
    private volatile int exampleGeneration = 0;
    MobileStudio studio;
    MobileExtras extras;
    String lastPronounced = "";
    float textScale = 1f;
    private int practiceGeneration = 0;
    private int lookupGeneration;
    CardStore store;
    NaturalSpeech speech;
    boolean busy, resumed;
    final Handler handler = new Handler(Looper.getMainLooper());
    final ExecutorService worker = Executors.newFixedThreadPool(2);
    LinearLayout root, content, bottom;
    ScrollView scroll;
    private TextView syncStatus;
    int page = 0, studyIndex = 0;
    private boolean studyStarted = false, flipped = false, favoritesOnly = false;
    private String studyDeck = "", libraryDeck = "", librarySearch = "",
                   studyMode = "Bugünkü tekrarlar", editing = "";
    private final ArrayList<String> queue = new ArrayList<>();
    private final Map<String, EditText> form = new LinkedHashMap<>();
    private JSONObject draft, originalCard;
    private Spinner formDeck, sourceLanguage, targetLanguage, partOfSpeech;
    final List<String> languageNames = new ArrayList<>();
    final Map<String, String> languageCodes = new LinkedHashMap<>();
    private List<JSONObject> formDecks = new ArrayList<>();
    private final Runnable periodicSync = new Runnable() {
        @Override
        public void run() {
            syncNow(false);
            if (resumed)
                handler.postDelayed(this, 15000);
        }
    };

    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        store = new CardStore(this);
        uiLanguage = store.config("ui_language", "tr");
        locale = new L10n(this, uiLanguage);
        loadLanguages();
        if (state != null) {
            moduleSearch = state.getString("moduleSearch", "");
            modulePage = state.getInt("modulePage", 0);
            libraryStatus = state.getString("libraryStatus", "");
            libraryLanguage = state.getString("libraryLanguage", "");
            libraryLimit = state.getInt("libraryLimit", 40);
            page = state.getInt("page", 0);
            transferFormat = state.getString("transferFormat", "json");
            transferDeck = state.getString("transferDeck", "");
            practiceKind = state.getString("practiceKind", "writing");
            practiceIndex = state.getInt("practiceIndex");
            practiceScore = state.getInt("practiceScore");
            String practiceSaved = state.getString("practiceCards", "[]");
            try {
                JSONArray savedPractice = new JSONArray(practiceSaved);
                for (int i = 0; i < savedPractice.length(); i++)
                    practiceCards.add(savedPractice.getJSONObject(i));
            } catch (Exception ignored) {
            }
            editing = state.getString("editing", "");
            studyIndex = state.getInt("studyIndex", 0);
            flipped = state.getBoolean("flipped");
            studyStarted = state.getBoolean("studyStarted");
            ArrayList<String> saved = state.getStringArrayList("queue");
            if (saved != null)
                queue.addAll(saved);
            studyDeck = state.getString("studyDeck", "");
            studyMode = state.getString("studyMode", "Bugünkü tekrarlar");
            libraryDeck = state.getString("libraryDeck", "");
            librarySearch = state.getString("librarySearch", "");
            favoritesOnly = state.getBoolean("favoritesOnly");
            String value = state.getString("draft");
            if (value != null)
                draft = CardStore.json(value);
            String original = state.getString("originalCard");
            if (original != null)
                originalCard = CardStore.json(original);
        }
        speech = new NaturalSpeech(getApplicationContext());
        studio = new MobileStudio(this);
        extras = new MobileExtras(this);
        applyPreferences();
        if (state != null && state.getString("studio") != null)
            studio.restore(CardStore.json(state.getString("studio")));
        if (state == null)
            page = startupPage();
        worker.execute(() -> {
            SentenceExamples.local(this, "", "en");
            SentenceExamples.translation(this, "", "tr");
        });
        buildRoot();
        render();
        MobileReminders.schedule(this, store);
        MobileReminders.scheduleTimer(this, store);
        if (getIntent().hasExtra("route"))
            openRoute(getIntent().getStringExtra("route"));
        openWidgetCard(getIntent());
    }

    @Override
    protected void onResume() {
        super.onResume();
        resumed = true;
        if (studio != null && page == 12)
            render();
        if (extras != null && page == 14)
            render();
    }
    @Override
    protected void onPause() {
        captureDraft();
        if (studio != null) {
            studio.pause();
            if (!busy)
                studio.saveTable(false);
        }
        resumed = false;
        if (speech != null)
            speech.stop();
        handler.removeCallbacks(periodicSync);
        if (extras != null)
            handler.removeCallbacks(extras.timerTick);
        StudyWidget.refresh(this);
        super.onPause();
    }
    @Override
    protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        worker.shutdownNow();
        if (speech != null)
            speech.close();
        super.onDestroy();
    }
    @Override
    protected void onSaveInstanceState(Bundle out) {
        captureDraft();
        if (studio != null)
            out.putString("studio", studio.state().toString());
        out.putString("transferFormat", transferFormat);
        out.putString("transferDeck", transferDeck);
        out.putString("practiceKind", practiceKind);
        out.putInt("practiceIndex", practiceIndex);
        out.putInt("practiceScore", practiceScore);
        out.putString("practiceCards", new JSONArray(practiceCards).toString());
        out.putString("moduleSearch", moduleSearch);
        out.putInt("modulePage", modulePage);
        out.putString("libraryStatus", libraryStatus);
        out.putString("libraryLanguage", libraryLanguage);
        out.putInt("libraryLimit", libraryLimit);
        out.putInt("page", page);
        out.putString("editing", editing);
        out.putInt("studyIndex", studyIndex);
        out.putBoolean("flipped", flipped);
        out.putBoolean("studyStarted", studyStarted);
        out.putStringArrayList("queue", queue);
        out.putString("studyDeck", studyDeck);
        out.putString("studyMode", studyMode);
        out.putString("libraryDeck", libraryDeck);
        out.putString("librarySearch", librarySearch);
        out.putBoolean("favoritesOnly", favoritesOnly);
        if (draft != null)
            out.putString("draft", draft.toString());
        super.onSaveInstanceState(out);
        if (originalCard != null)
            out.putString("originalCard", originalCard.toString());
    }

    private void loadLanguages() {
        try (InputStream in = getAssets().open("languages.json")) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] bytes = new byte[4096];
            int read;
            while ((read = in.read(bytes)) != -1) out.write(bytes, 0, read);
            JSONArray languages = new JSONArray(out.toString("UTF-8"));
            for (int i = 0; i < languages.length(); i++) {
                JSONObject item = languages.getJSONObject(i);
                String name = item.getString(uiLanguage);
                languageNames.add(name);
                languageCodes.put(name, item.getString("code"));
                for (String key : new String[] {"tr", "en", "de", "es", "code"})
                    languageCodes.put(item.getString(key), item.getString("code"));
            }
        } catch (Exception e) {
            languageNames.add("İngilizce");
            languageNames.add("Türkçe");
            languageCodes.put("İngilizce", "en");
            languageCodes.put("Türkçe", "tr");
        }
    }

    void applyPreferences() {
        String theme = store.config("theme", "dark_slate");
        BG = Color.parseColor(theme.equals("midnight") ? "#081426"
                        : theme.equals("graphite")     ? "#17191e"
                                                       : "#0d121c");
        PANEL = Color.parseColor(theme.equals("midnight") ? "#102039"
                        : theme.equals("graphite")        ? "#22252c"
                                                          : "#121824");
        try {
            GREEN = Color.parseColor(store.config("accent_color", "#10b981"));
        } catch (IllegalArgumentException invalid) {
            GREEN = Color.rgb(16, 185, 129);
        }
        textScale = Math.max(.9f, Math.min(1.3f, store.number("text_scale", 100) / 100f));
        uiLanguage = store.config("ui_language", "tr");
        locale = new L10n(this, uiLanguage);
        languageNames.clear();
        languageCodes.clear();
        loadLanguages();
        speech.configure(store.decimal("speech_speed", 1), store.number("speech_volume", 100));
    }
    int startupPage() {
        switch (store.config("startup_page", "study")) {
            case "library":
                return 2;
            case "tables":
                return 9;
            case "stats":
                return 13;
            case "import":
                return 5;
            case "settings":
                return 4;
            default:
                return 0;
        }
    }
    void icon(Button button, String key) {
        int id = getResources().getIdentifier("ic_" + key, "drawable", getPackageName());
        if (id == 0)
            return;
        android.graphics.drawable.Drawable icon = getDrawable(id).mutate();
        icon.setTint(button.getCurrentTextColor() == BG ? BG : GREEN);
        icon.setBounds(0, 0, dp(22), dp(22));
        button.setCompoundDrawables(icon, null, null, null);
        button.setCompoundDrawablePadding(dp(7));
        button.setPadding(dp(12), 0, dp(12), 0);
    }
    CheckBox check(LinearLayout box, String label, boolean enabled) {
        CheckBox checkbox = new CheckBox(this);
        checkbox.setText(t(label));
        checkbox.setTextColor(INK);
        checkbox.setTextSize(15 * textScale);
        checkbox.setButtonTintList(android.content.res.ColorStateList.valueOf(GREEN));
        checkbox.setChecked(enabled);
        checkbox.setMinHeight(dp(48));
        box.addView(checkbox);
        return checkbox;
    }
    Spinner languagePicker(LinearLayout box, String label, String code) {
        box.addView(text(t(label), 13, MUTED));
        Spinner spinner = spinner(languageNames, languageName(code));
        box.addView(spinner);
        return spinner;
    }
    String languageCode(Spinner spinner) {
        return languageCodes.getOrDefault(spinner.getSelectedItem().toString(), "en");
    }
    void requestNotifications() {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS)
                        != android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[] {android.Manifest.permission.POST_NOTIFICATIONS}, 201);
    }
    private void openWidgetCard(Intent intent) {
        String id = intent.getStringExtra("widget_card");
        if (id != null && store.get(id) != null) {
            queue.clear();
            queue.add(id);
            studyStarted = true;
            studyIndex = 0;
            flipped = false;
            navigate(0);
        }
    }
    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        openRoute(intent.getStringExtra("route"));
        openWidgetCard(intent);
    }
    @Override
    public void onBackPressed() {
        if (busy)
            return;
        if (page == 12) {
            navigate(studio.preview ? 11
                            : studio.playing != null
                                    && store.get(studio.playing.optString("id")) != null
                            ? 9
                            : 2);
            return;
        }
        if (page == 10 || page == 11) {
            navigate(9);
            return;
        }
        if (page == 7 || page == 8 || page == 9) {
            navigate(6);
            return;
        }
        if (page != 0) {
            navigate(0);
            return;
        }
        super.onBackPressed();
    }

    String t(String key, Object... values) {
        return locale.get(key, values);
    }
    String languageName(String value) {
        String code = languageCodes.get(value);
        if (code == null)
            code = value;
        for (String name : languageNames)
            if (code.equals(languageCodes.get(name)))
                return name;
        return value;
    }
    int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + .5f);
    }
    GradientDrawable background(int color, int radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(radius));
        return d;
    }
    LinearLayout column() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        return l;
    }
    LinearLayout row() {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.HORIZONTAL);
        l.setGravity(Gravity.CENTER_VERTICAL);
        return l;
    }
    TextView text(String value, int size, int color) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(size * textScale);
        t.setTextColor(color);
        t.setPadding(0, dp(5), 0, dp(7));
        return t;
    }
    TextView title(String value) {
        TextView t = text(value, 27, INK);
        t.setTypeface(null, Typeface.BOLD);
        content.addView(t);
        return t;
    }
    void hint(String value) {
        content.addView(text(value, 14, MUTED));
    }
    Button button(String label, boolean primary, Runnable action) {
        Button b = new Button(this);
        b.setText(label);
        b.setSingleLine(false);
        b.setAllCaps(false);
        b.setTextColor(primary ? BG : INK);
        b.setTextSize(14 * textScale);
        b.setMinHeight(dp(48));
        b.setBackground(background(primary ? GREEN : Color.rgb(29, 39, 57), 12));
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.setMargins(0, dp(6), 0, dp(6));
        b.setLayoutParams(p);
        b.setOnClickListener(v -> {
            if (!busy)
                action.run();
        });
        return b;
    }
    void addButton(String label, boolean primary, Runnable action) {
        content.addView(button(label, primary, action));
    }
    LinearLayout panel() {
        LinearLayout p = column();
        p.setBackground(background(PANEL, 18));
        p.setPadding(dp(18), dp(16), dp(18), dp(16));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.setMargins(0, dp(8), 0, dp(8));
        p.setLayoutParams(lp);
        return p;
    }
    void toast(String message) {
        Toast.makeText(this, t(message), Toast.LENGTH_LONG).show();
    }

    void buildRoot() {
        root = column();
        root.setBackgroundColor(BG);
        // Android 15/16 system bars and display cutouts must not cover controls.
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            root.setOnApplyWindowInsetsListener((v, insets) -> {
                android.graphics.Insets space = insets.getInsets(WindowInsets.Type.systemBars()
                        | WindowInsets.Type.displayCutout() | WindowInsets.Type.ime());
                root.setPadding(space.left, space.top, space.right, space.bottom);
                return insets;
            });
        }
        LinearLayout header = column();
        header.setPadding(dp(20), dp(10), dp(20), dp(8));
        LinearLayout brand = row();
        TextView logo =
                text(store.config("profile_name", "").isEmpty() ? t("Study Card")
                                                                : store.config("profile_name", ""),
                        22, GREEN);
        logo.setTypeface(null, Typeface.BOLD);
        brand.addView(logo, new LinearLayout.LayoutParams(0, -2, 1));
        Button menu = button(t("Menu"), false, this::showMenu);
        icon(menu, "extensions");
        brand.addView(menu, new LinearLayout.LayoutParams(dp(116), dp(50)));
        header.addView(brand);
        syncStatus = text(t("Offline library · words saved on this device"), 12, MUTED);
        header.addView(syncStatus);
        root.addView(header);
        scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        content = column();
        content.setPadding(dp(20), dp(12), dp(20), dp(24));
        scroll.addView(content);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        bottom = row();
        bottom.setPadding(dp(4), dp(5), dp(4), dp(5));
        root.addView(bottom);
        setContentView(root);
    }

    void navigate(int next) {
        if (busy)
            return;
        practiceGeneration++;
        practicePreparing = false;
        captureDraft();
        if (studio != null) {
            studio.pause();
            studio.saveTable(false);
            studio.captureAction = null;
        }
        if (extras != null)
            handler.removeCallbacks(extras.timerTick);
        if (speech != null)
            speech.stop();
        page = next;
        lastPronounced = "";
        render();
        ((InputMethodManager) getSystemService(INPUT_METHOD_SERVICE))
                .hideSoftInputFromWindow(root.getWindowToken(), 0);
    }
    void render() {
        form.clear();
        content.removeAllViews();
        bottom.removeAllViews();
        if (studio != null)
            studio.captureAction = null;
        if (store.flag("keep_screen_on", false)
                && (page == 0 || page == 7 || page == 12 || page == 14))
            getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        else
            getWindow().clearFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        String[] tabs = {"Çalış", "Ekle", "Kütüphane", "Desteler", "Settings"};
        for (int i = 0; i < tabs.length; i++) {
            final int next = i;
            if (!store.flag("menu_visible_"
                                + new String[] {"study", "add", "library", "decks", "settings"}[i],
                        true))
                continue;
            Button b = button(t(tabs[i]), page == i, () -> navigate(next));
            b.setTextSize(11);
            b.setPadding(0, 0, 0, 0);
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(52), 1);
            p.setMargins(dp(2), 0, dp(2), 0);
            bottom.addView(b, p);
        }
        switch (page) {
            case 0:
                study();
                break;
            case 1:
                addCard();
                break;
            case 2:
                library();
                break;
            case 3:
                decks();
                break;
            case 5:
                transfer();
                break;
            case 6:
                extensions();
                break;
            case 7:
                practice();
                break;
            case 8:
                moduleTable();
                break;
            case 9:
                studio.home();
                break;
            case 10:
                studio.tableEditor();
                break;
            case 11:
                studio.designer();
                break;
            case 12:
                studio.player();
                break;
            case 13:
                extras.statistics();
                break;
            case 14:
                extras.timer();
                break;
            case 15:
                extras.sentenceMemory();
                break;
            case 17:
                extras.filteredCards("favorites");
                break;
            case 18:
                extras.filteredCards("mistakes");
                break;
            default:
                account();
        }
        scroll.scrollTo(0, 0);
        if (page != 1) {
            exampleGeneration++;
            lookupGeneration++;
        }
    }

    Spinner spinner(List<String> values, String selected) {
        Spinner s = new Spinner(this);
        ArrayList<String> options = new ArrayList<>(values);
        if (selected != null && !selected.isEmpty() && !options.contains(selected))
            options.add(selected);
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(
                this, android.R.layout.simple_spinner_item, options) {
            private View style(View view) {
                TextView label = (TextView) view;
                label.setTextColor(INK);
                label.setTextSize(15 * textScale);
                label.setPadding(dp(12), dp(12), dp(12), dp(12));
                label.setMinHeight(dp(48));
                label.setBackgroundColor(PANEL);
                return label;
            }
            @Override
            public View getView(int position, View recycled, android.view.ViewGroup parent) {
                return style(super.getView(position, recycled, parent));
            }
            @Override
            public View getDropDownView(
                    int position, View recycled, android.view.ViewGroup parent) {
                return style(super.getDropDownView(position, recycled, parent));
            }
        };
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        s.setAdapter(adapter);
        s.setBackground(background(Color.rgb(23, 31, 46), 10));
        s.setMinimumHeight(dp(48));
        s.setPopupBackgroundDrawable(background(PANEL, 10));
        if (selected != null)
            s.setSelection(Math.max(0, options.indexOf(selected)));
        return s;
    }
    void selection(Spinner s, java.util.function.Consumer<Integer> listener) {
        s.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            boolean initial = true;
            @Override
            public void onItemSelected(AdapterView<?> p, View v, int pos, long id) {
                if (initial) {
                    initial = false;
                    return;
                }
                listener.accept(pos);
            }
            @Override
            public void onNothingSelected(AdapterView<?> p) {}
        });
    }
    private List<String> deckNames(List<JSONObject> decks, boolean all) {
        List<String> names = new ArrayList<>();
        if (all)
            names.add("Tüm desteler");
        for (JSONObject d : decks) names.add(d.optString("name"));
        return names;
    }
    String deckName(String id) {
        JSONObject d = store.get(id);
        return d == null ? t("Deck") : d.optString("name");
    }
    boolean due(JSONObject card) {
        return card.optString("due_date", LocalDate.now().toString())
                        .compareTo(LocalDate.now().toString())
                <= 0
                || "new".equals(card.optString("status"));
    }

    private void startStudy() {
        queue.clear();
        studyIndex = 0;
        flipped = false;
        studyStarted = true;
        List<JSONObject> cards = store.list("card");
        Collections.sort(
                cards, (a, b) -> a.optString("due_date").compareTo(b.optString("due_date")));
        int goal = Math.max(5, Math.min(200, store.number("session_size", 50)));
        if (store.flag("shuffle_cards", true))
            Collections.shuffle(cards);
        for (JSONObject card : cards) {
            if (!studyDeck.isEmpty() && !studyDeck.equals(card.optString("deck_uuid")))
                continue;
            if (studyMode.equals("Bugünkü tekrarlar") && !due(card))
                continue;
            if (studyMode.equals("Favoriler") && card.optInt("is_favorite") != 1)
                continue;
            queue.add(card.optString("uuid"));
            if (queue.size() >= goal)
                break;
        }
    }

    private void study() {
        title(t("A few words every day"));
        hint(t("Flip the card and rate your recall. The review date adapts to you."));
        List<JSONObject> decks = store.list("deck");
        List<String> names = deckNames(decks, true);
        Spinner filter = spinner(names, studyDeck.isEmpty() ? names.get(0) : deckName(studyDeck));
        content.addView(filter);
        selection(filter, pos -> {
            studyDeck = pos == 0 ? "" : decks.get(pos - 1).optString("uuid");
            startStudy();
            render();
        });
        String[] modes = {"Bugünkü tekrarlar", "Tüm kelimeler", "Favoriler"};
        Spinner mode = spinner(
                java.util.Arrays.asList(t(modes[0]), t(modes[1]), t(modes[2])), t(studyMode));
        content.addView(mode);
        selection(mode, pos -> {
            studyMode = modes[pos];
            startStudy();
            render();
        });
        if (!studyStarted)
            startStudy();
        while (studyIndex < queue.size() && store.get(queue.get(studyIndex)) == null) studyIndex++;
        String day = LocalDate.now().toString();
        int today = day.equals(store.config("review_day", ""))
                ? Integer.parseInt(store.config("review_count", "0"))
                : 0;
        hint(t("Today: {count} reviews · Daily goal: {goal}", "count", today, "goal",
                store.config("daily_goal", "10")));
        ProgressBar dailyProgress =
                new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        dailyProgress.setProgressTintList(android.content.res.ColorStateList.valueOf(GREEN));
        dailyProgress.setMax(Math.max(1, store.number("daily_goal", 10)));
        dailyProgress.setProgress(today);
        content.addView(dailyProgress);
        if (studyIndex >= queue.size()) {
            LinearLayout empty = panel();
            empty.addView(text(queue.isEmpty() ? t("All done for today!") : t("Session complete!"),
                    23, GREEN));
            empty.addView(text(
                    t("Add new words or start a new session with your whole library."), 16, MUTED));
            content.addView(empty);
            addButton(t("New session"), true, () -> {
                startStudy();
                render();
            });
            addButton(t("Add word"), false, () -> navigate(1));
            return;
        }
        String id = queue.get(studyIndex);
        JSONObject card = store.get(id);
        ProgressBar progress =
                new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(queue.size());
        progress.setProgress(studyIndex);
        content.addView(progress);
        hint((studyIndex + 1) + " / " + queue.size() + " · "
                + deckName(card.optString("deck_uuid")));
        LinearLayout face = panel();
        face.setMinimumHeight(dp(240));
        face.setGravity(Gravity.CENTER);
        TextView term = text(card.optString("term"), 30, INK);
        term.setTypeface(null, Typeface.BOLD);
        term.setGravity(Gravity.CENTER);
        face.addView(term);
        if (store.flag("show_phonetics", true) && !card.optString("phonetic").isEmpty())
            face.addView(text(card.optString("phonetic"), 16, MUTED));
        if (flipped) {
            TextView meaning = text(card.optString("definition"), 23, GREEN);
            meaning.setGravity(Gravity.CENTER);
            face.addView(meaning);
            String usage = card.optString("example_sentence");
            String sourceCode = languageCodes.getOrDefault(
                    card.optString("source_lang"), card.optString("source_lang", "en"));
            boolean savedUsage = SentenceExamples.useful(card.optString("term"), usage, sourceCode);
            if (!savedUsage) {
                List<String> local =
                        SentenceExamples.local(this, card.optString("term"), sourceCode);
                usage = local.isEmpty() ? "" : local.get(0);
            }
            if (!usage.isEmpty())
                face.addView(text(usage, 16, INK));
            if (savedUsage && !card.optString("example_translation").isEmpty())
                face.addView(text(card.optString("example_translation"), 16, INK));
            if (store.flag("show_card_notes", true) && !card.optString("notes").isEmpty())
                face.addView(text(card.optString("notes"), 16, INK));
        } else
            face.addView(text(t("Anlamı görmek için karta dokun"), 14, MUTED));
        face.setContentDescription(t(flipped ? "Kartın anlamı. Ön yüze dönmek için dokun."
                                             : "Kartın ön yüzü. Anlamı görmek için dokun."));
        face.setOnClickListener(v -> {
            Runnable flip = () -> {
                flipped = !flipped;
                render();
            };
            if (store.flag("reduced_motion", false))
                flip.run();
            else
                face.animate().scaleX(.03f).setDuration(130).withEndAction(flip).start();
        });
        content.addView(face);
        String trigger = store.config("pronounce_trigger", "flip"),
               pronunciationKey = id + ":" + flipped;
        if (store.flag("auto_pronounce", false) && !pronunciationKey.equals(lastPronounced)
                && (trigger.equals("both") || flipped && trigger.equals("flip")
                        || !flipped && trigger.equals("appear"))) {
            lastPronounced = pronunciationKey;
            handler.post(() -> {
                if (page == 0)
                    speak(card);
            });
        }
        addButton(t("Listen"), false, () -> speak(card));
        if (flipped) {
            LinearLayout ratings = row();
            for (int rating = 1; rating <= 3; rating++) {
                final int value = rating;
                Button b = button(new String[] {t("Reps"), t("Hard"), t("I know it")}[rating - 1],
                        rating == 3, () -> {
                            store.rate(id, value);
                            StudyWidget.refresh(this);
                            extras.sound(value == 3);
                            if (value == 1)
                                queue.add(id);
                            studyIndex++;
                            flipped = false;
                            render();
                            syncSoon();
                        });
                LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, dp(50), 1);
                p.setMargins(dp(3), dp(8), dp(3), dp(8));
                ratings.addView(b, p);
            }
            content.addView(ratings);
        }
        addButton(card.optInt("is_favorite") == 1 ? t("★ Remove favorite") : t("☆ Add favorite"),
                false, () -> {
                    JSONObject latest = store.get(id);
                    if (latest == null) {
                        render();
                        return;
                    }
                    CardStore.put(latest, "is_favorite", latest.optInt("is_favorite") == 1 ? 0 : 1);
                    store.save("card", id, latest);
                    render();
                    syncSoon();
                });
        addButton(t("Edit card"), false, () -> edit(card));
    }

    void speak(JSONObject card) {
        String source = card.optString("source_lang", "en");
        String code = languageCodes.getOrDefault(source, source.length() <= 5 ? source : "en");
        speech.play(card.optString("term"), code, this::toast);
    }
    private void prefetchPractice(JSONObject card) {
        String source = card.optString(
                "source_lang", practiceKind.contains("_") ? practiceKind.substring(0, 2) : "en");
        String code = languageCodes.getOrDefault(source, source);
        speech.prefetch(practiceKind.equals("shadowing") || practiceKind.equals("cloze")
                        ? usageSentence(card)
                        : card.optString("term"),
                code);
    }

    String usageSentence(JSONObject card) {
        String word = card.optString("term"), raw = card.optString("source_lang", "en"),
               language = languageCodes.getOrDefault(raw, raw);
        String sentence = card.optString("example_sentence", card.optString("example"));
        if (SentenceExamples.useful(word, sentence, language))
            return sentence;
        List<JSONObject> remembered = store.sentences(word, language);
        for (JSONObject row : remembered)
            if (SentenceExamples.useful(word, row.optString("text"), language))
                return row.optString("text");
        List<String> local = SentenceExamples.local(this, word, language);
        return local.isEmpty() ? "" : local.get(0);
    }

    private static final String[] PART_KEYS = {"word", "noun", "verb", "adjective", "adverb",
            "idiom", "phrase", "phrasal_verb", "article", "conjunction"};
    private String partName(String stored) {
        String value = CardStore.wordKey(t(stored));
        for (String key : PART_KEYS)
            if (key.equals(stored) || CardStore.wordKey(t(key)).equals(value))
                return t(key);
        return t(stored);
    }

    EditText field(LinearLayout parent, String label, String value, boolean multiline) {
        if (!label.isEmpty())
            parent.addView(text(label, 13, MUTED));
        EditText e = new EditText(this);
        e.setText(value);
        e.setTextColor(INK);
        e.setHintTextColor(MUTED);
        e.setTextSize(16 * textScale);
        e.setPadding(dp(12), dp(10), dp(12), dp(10));
        e.setBackground(background(Color.rgb(23, 31, 46), 10));
        e.setInputType(InputType.TYPE_CLASS_TEXT
                | (multiline ? InputType.TYPE_TEXT_FLAG_MULTI_LINE
                                        | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
                             : InputType.TYPE_TEXT_FLAG_CAP_SENTENCES));
        e.setMinHeight(dp(48));
        if (multiline) {
            e.setMinLines(2);
            e.setGravity(Gravity.TOP);
        } else
            e.setSingleLine(true);
        e.setFilters(
                new android.text.InputFilter[] {new android.text.InputFilter.LengthFilter(16000)});
        parent.addView(e);
        return e;
    }

    private JSONObject newCard() {
        JSONObject card = new JSONObject();
        for (String key : new String[] {"term", "definition", "example_sentence",
                     "example_translation", "phonetic", "notes"})
            CardStore.put(card, key, "");
        CardStore.put(card, "part_of_speech", "word");
        CardStore.put(card, "source_lang", "en");
        CardStore.put(card, "target_lang", "tr");
        CardStore.put(card, "status", "new");
        CardStore.put(card, "is_favorite", 0);
        CardStore.put(card, "repetition_count", 0);
        CardStore.put(card, "interval_days", 1);
        CardStore.put(card, "ease_factor", 2.5);
        CardStore.put(card, "due_date", LocalDate.now().toString());
        CardStore.put(card, "last_reviewed", JSONObject.NULL);
        CardStore.put(card, "created_at", LocalDateTime.now().toString());
        return card;
    }
    void edit(JSONObject card) {
        captureDraft();
        studio.pause();
        speech.stop();
        editing = card.optString("uuid");
        draft = CardStore.json(card.toString());
        originalCard = CardStore.json(card.toString());
        page = 1;
        render();
    }
    private void captureDraft() {
        if (page != 1 || form.isEmpty() || formDecks.isEmpty())
            return;
        if (draft == null)
            draft = newCard();
        for (Map.Entry<String, EditText> entry : form.entrySet())
            CardStore.put(draft, entry.getKey(), entry.getValue().getText().toString().trim());
        int selected = formDeck.getSelectedItemPosition();
        if (selected >= 0 && selected < formDecks.size())
            CardStore.put(draft, "deck_uuid", formDecks.get(selected).optString("uuid"));
        CardStore.put(draft, "source_lang",
                languageCodes.get(sourceLanguage.getSelectedItem().toString()));
        CardStore.put(draft, "target_lang",
                languageCodes.get(targetLanguage.getSelectedItem().toString()));
        CardStore.put(draft, "part_of_speech",
                PART_KEYS[Math.max(0,
                        Math.min(PART_KEYS.length - 1, partOfSpeech.getSelectedItemPosition()))]);
    }

    private void addCard() {
        title(editing.isEmpty() ? t("New word") : t("Edit card"));
        hint(t("Offline library · words saved on this device"));
        formDecks = store.list("deck");
        if (formDecks.isEmpty()) {
            hint(t("Create a deck first."));
            addButton(t("Create deck"), true, () -> navigate(3));
            return;
        }
        if (draft == null)
            draft = newCard();
        if (!editing.isEmpty() && store.get(editing) == null) {
            hint(t("This card was deleted on another device. Save your draft as a new card."));
            editing = "";
        }
        content.addView(text(t("Deck"), 13, MUTED));
        formDeck = spinner(deckNames(formDecks, false),
                deckName(draft.optString("deck_uuid", formDecks.get(0).optString("uuid"))));
        content.addView(formDeck);
        String[] keys = {"term", "definition", "phonetic", "example_sentence",
                "example_translation", "notes"};
        String[] labels = {"Kelime / ifade *", "Anlamı *", "Fonetik (isteğe bağlı)", "Örnek cümle",
                "Örnek cümlenin çevirisi", "Notlar"};
        for (int i = 0; i < keys.length; i++)
            form.put(keys[i], field(content, t(labels[i]), draft.optString(keys[i]), i >= 3));
        content.addView(text(t("Word language"), 13, MUTED));
        sourceLanguage = spinner(languageNames, languageName(draft.optString("source_lang", "en")));
        content.addView(sourceLanguage);
        content.addView(text(t("Meaning language"), 13, MUTED));
        targetLanguage = spinner(languageNames, languageName(draft.optString("target_lang", "tr")));
        content.addView(targetLanguage);
        List<String> parts = new ArrayList<>();
        for (String key : PART_KEYS) parts.add(t(key));
        content.addView(text(t("Part of speech"), 13, MUTED));
        partOfSpeech = spinner(parts, partName(draft.optString("part_of_speech", "word")));
        content.addView(partOfSpeech);
        TextView duplicateLabel = text("", 14, Color.rgb(251, 191, 36));
        content.addView(duplicateLabel);
        LinearLayout examples = column();
        content.addView(examples);
        Runnable updateWord = () -> {
            String word = form.get("term").getText().toString();
            List<JSONObject> matches = store.duplicates(word, editing);
            StringBuilder names = new StringBuilder();
            for (JSONObject match : matches)
                names.append("\n")
                        .append(match.optString("term"))
                        .append(" — ")
                        .append(match.optString("definition"))
                        .append(" · ")
                        .append(deckName(match.optString("deck_uuid")));
            duplicateLabel.setText(
                    matches.isEmpty() ? "" : t("This word is already in your library:") + names);
            duplicateLabel.setOnClickListener(v -> {
                if (!matches.isEmpty())
                    edit(matches.get(0));
            });
            int generation = ++exampleGeneration;
            handler.postDelayed(() -> loadExamples(word, examples, generation), 300);
        };
        form.get("term").addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int c, int f) {}
            public void onTextChanged(CharSequence s, int a, int b, int c) {
                updateWord.run();
            }
            public void afterTextChanged(Editable e) {}
        });
        selection(sourceLanguage, pos -> updateWord.run());
        selection(targetLanguage, pos -> updateWord.run());
        updateWord.run();
        addButton(t("Find meaning and pronunciation"), false, this::lookupWord);
        addButton(editing.isEmpty() ? t("Save word") : t("Save changes"), true, () -> {
            captureDraft();
            List<JSONObject> matches = store.duplicates(draft.optString("term"), editing);
            if (!matches.isEmpty())
                new AlertDialog.Builder(this)
                        .setTitle(t("Word already exists"))
                        .setMessage(
                                t("This word is already in your library. Add another card anyway?"))
                        .setNegativeButton(t("Cancel"), null)
                        .setPositiveButton(t("Save"), (dialog, which) -> saveDraft())
                        .show();
            else
                saveDraft();
        });
        if (!editing.isEmpty())
            addButton(t("Finish editing"), false, () -> {
                editing = "";
                draft = null;
                originalCard = null;
                form.clear();
                navigate(2);
            });
    }

    private void lookupWord() {
        String word = form.get("term").getText().toString().trim();
        if (word.isEmpty()) {
            form.get("term").setError(t("This field is required"));
            return;
        }
        String source = languageCode(sourceLanguage), target = languageCode(targetLanguage);
        int ticket = ++lookupGeneration;
        toast("Looking up the word…");
        worker.execute(() -> {
            try {
                JSONObject result = WordLookup.find(this, word, source, target);
                handler.post(() -> {
                    if (ticket != lookupGeneration || page != 1 || isDestroyed()
                            || !word.equals(form.get("term").getText().toString().trim())
                            || !source.equals(languageCode(sourceLanguage))
                            || !target.equals(languageCode(targetLanguage)))
                        return;
                    boolean filled = false;
                    for (String key : new String[] {"definition", "phonetic"})
                        if (form.get(key).getText().toString().trim().isEmpty()
                                && !result.optString(key).isEmpty()) {
                            form.get(key).setText(result.optString(key));
                            filled = true;
                        }
                    int part = Arrays.asList(PART_KEYS).indexOf(result.optString("part_of_speech"));
                    if (part >= 0 && partOfSpeech.getSelectedItemPosition() == 0)
                        partOfSpeech.setSelection(part);
                    toast(filled ? "Dictionary details added. Review them before saving."
                                 : "No additional dictionary details found. You can fill the fields manually.");
                });
            } catch (Exception error) {
                handler.post(() -> {
                    if (ticket == lookupGeneration && page == 1 && !isDestroyed())
                        toast("Dictionary unavailable. You can fill the fields manually.");
                });
            }
        });
    }

    private void loadExamples(String word, LinearLayout container, int generation) {
        if (generation != exampleGeneration || page != 1 || word.trim().isEmpty())
            return;
        String language = languageCodes.get(sourceLanguage.getSelectedItem().toString());
        if (language == null)
            return;
        String target = languageCode(targetLanguage);
        List<String> local = SentenceExamples.local(this, word, language);
        for (JSONObject row : store.sentences(word, language))
            if (!local.contains(row.optString("text"))
                    && SentenceExamples.useful(word, row.optString("text"), language))
                local.add(0, row.optString("text"));
        showExamples(local, container);
        if (local.size() >= 10)
            return;
        worker.execute(() -> {
            if (generation != exampleGeneration)
                return;
            List<String> fetched = new ArrayList<>(local);
            String error = null;
            try {
                for (String sentence : SentenceExamples.online(word, language, target))
                    if (!fetched.contains(sentence) && fetched.size() < 10)
                        fetched.add(sentence);
            } catch (Exception failure) {
                error = t("Examples could not be fetched. Try again when connected.");
            }
            final String message = error;
            handler.post(() -> {
                if (page == 1 && generation == exampleGeneration && !isDestroyed()) {
                    for (String sentence : fetched)
                        store.rememberSentence(word, language, sentence, target,
                                SentenceExamples.translation(this, sentence, target));
                    showExamples(fetched, container);
                    if (fetched.isEmpty() && message != null)
                        container.addView(text(message, 13, MUTED));
                }
            });
        });
    }
    private void showExamples(List<String> examples, LinearLayout container) {
        container.removeAllViews();
        container.addView(text(t("Usage examples"), 16, INK));
        if (examples.isEmpty())
            container.addView(text(
                    t("No contextual examples yet. Add a full usage sentence or connect to search."),
                    13, MUTED));
        for (String example : examples)
            container.addView(button(example, false, () -> {
                form.get("example_sentence").setText(example);
                String target = languageCode(targetLanguage),
                       translation = SentenceExamples.translation(this, example, target);
                if (translation.isEmpty())
                    for (JSONObject row : store.sentences(form.get("term").getText().toString(),
                                 languageCode(sourceLanguage)))
                        if (example.equals(row.optString("text"))
                                && row.optJSONObject("translations") != null)
                            translation = row.optJSONObject("translations").optString(target);
                form.get("example_translation").setText(translation);
            }));
    }

    private void saveDraft() {
        captureDraft();
        for (String key : new String[] {"term", "definition"})
            if (draft.optString(key).isEmpty()) {
                form.get(key).setError(t("This field is required"));
                form.get(key).requestFocus();
                return;
            }
        if (store.get(draft.optString("deck_uuid")) == null) {
            toast("Seçilen deste silinmiş. Başka bir deste seç.");
            return;
        }
        JSONObject saved = draft;
        if (!editing.isEmpty()) {
            JSONObject latest = store.get(editing);
            if (latest == null) {
                toast("Kart diğer cihazda silinmiş. Taslağın korundu; yeni kart olarak kaydet.");
                editing = "";
                return;
            }
            // Editing content must preserve reviews/favorites received while the form was open.
            for (String key : new String[] {"term", "definition", "phonetic", "example_sentence",
                         "example_translation", "notes", "deck_uuid", "source_lang", "target_lang",
                         "part_of_speech"}) {
                if (originalCard == null
                        || !String.valueOf(draft.opt(key))
                                .equals(String.valueOf(originalCard.opt(key))))
                    CardStore.put(latest, key, draft.opt(key));
            }
            saved = latest;
        }
        store.save("card", editing, saved);
        editing = "";
        draft = null;
        originalCard = null;
        form.clear();
        render();
        toast("Kelime kaydedildi");
        syncSoon();
    }

    private void library() {
        title(t("Your words"));
        hint(t("Search, edit and favorite your cards."));
        EditText search = field(content, t("Search word or meaning"), librarySearch, false);
        search.setInputType(InputType.TYPE_CLASS_TEXT);
        List<JSONObject> decks = store.list("deck");
        Spinner filter = spinner(deckNames(decks, true),
                libraryDeck.isEmpty() ? "Tüm desteler" : deckName(libraryDeck));
        content.addView(filter);
        CheckBox favorites = new CheckBox(this);
        favorites.setText(t("Favorites only"));
        favorites.setTextColor(INK);
        favorites.setChecked(favoritesOnly);
        content.addView(favorites);
        String[] statusValues = {"", "new", "learning", "mastered"};
        Spinner status = new StudioUi(this).options(content, "Status",
                new String[] {"All statuses", "New", "Learning", "Mastered"}, statusValues,
                libraryStatus);
        List<String> sourceNames = new ArrayList<>(), sourceCodes = new ArrayList<>();
        sourceNames.add(t("All languages"));
        sourceCodes.add("");
        for (JSONObject card : store.list("card")) {
            String code = languageCodes.getOrDefault(
                    card.optString("source_lang", "en"), card.optString("source_lang", "en"));
            if (!sourceCodes.contains(code)) {
                sourceCodes.add(code);
                sourceNames.add(languageName(code));
            }
        }
        Spinner language = spinner(
                sourceNames, sourceNames.get(Math.max(0, sourceCodes.indexOf(libraryLanguage))));
        content.addView(language);
        addButton(t("Daily challenge"), false, extras::dailyChallenge);
        addButton(t("Practice Quiz"), true, () -> extras.beginLibraryGame("quiz", libraryCards()));
        addButton(
                t("Speed Match"), false, () -> extras.beginLibraryGame("matching", libraryCards()));
        LinearLayout results = column();
        content.addView(results);
        Runnable fill = () -> {
            results.removeAllViews();
            int count = 0, total = 0;
            String needle = librarySearch.toLowerCase(Locale.ROOT);
            for (JSONObject card : libraryCards()) {
                if ((!libraryDeck.isEmpty() && !libraryDeck.equals(card.optString("deck_uuid")))
                        || (favoritesOnly && card.optInt("is_favorite") != 1))
                    continue;
                if (!(card.optString("term") + " " + card.optString("definition"))
                                .toLowerCase(Locale.ROOT)
                                .contains(needle))
                    continue;
                total++;
                if (count++ >= libraryLimit)
                    continue;
                String id = card.optString("uuid");
                LinearLayout p = panel();
                p.addView(
                        text(card.optString("term") + (card.optInt("is_favorite") == 1 ? " ★" : ""),
                                21, INK));
                p.addView(text(card.optString("definition"), 17, GREEN));
                p.addView(text(deckName(card.optString("deck_uuid")), 12, MUTED));
                p.addView(button(t("Edit"), false, () -> edit(card)));
                p.addView(button(
                        t(card.optInt("is_favorite") == 1 ? "★ Remove favorite" : "☆ Add favorite"),
                        false, () -> {
                            CardStore.put(
                                    card, "is_favorite", card.optInt("is_favorite") == 1 ? 0 : 1);
                            store.save("card", id, card);
                            render();
                        }));
                p.addView(button(t("Listen"), false, () -> speak(card)));
                p.addView(button(t("Delete"), false,
                        ()
                                -> new AlertDialog.Builder(this)
                                        .setTitle(t("Delete this card?"))
                                        .setMessage(t("{term} will be deleted from this device.",
                                                "term", card.optString("term")))
                                        .setNegativeButton(t("Cancel"), null)
                                        .setPositiveButton(t("Delete"),
                                                (dialog, which) -> {
                                                    store.delete(id);
                                                    render();
                                                    syncSoon();
                                                })
                                        .show()));
                results.addView(p);
            }
            results.addView(
                    text(t("{count} words", "count", total)
                                    + (total > libraryLimit ? " · " + t("More words below") : ""),
                            14, MUTED),
                    0);
            if (total > libraryLimit)
                results.addView(button(t("Show more"), false, () -> {
                    libraryLimit += 40;
                    render();
                }));
            if (total == 0)
                results.addView(button(t("Add your first word"), true, () -> navigate(1)));
        };
        fill.run();
        search.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int c, int f) {}
            public void onTextChanged(CharSequence s, int a, int b, int c) {
                librarySearch = s.toString();
                fill.run();
            }
            public void afterTextChanged(Editable e) {}
        });
        selection(filter, pos -> {
            libraryDeck = pos == 0 ? "" : decks.get(pos - 1).optString("uuid");
            fill.run();
        });
        favorites.setOnCheckedChangeListener((b, checked) -> {
            favoritesOnly = checked;
            libraryLimit = 40;
            fill.run();
        });
        selection(status, pos -> {
            libraryStatus = statusValues[pos];
            libraryLimit = 40;
            fill.run();
        });
        selection(language, pos -> {
            libraryLanguage = sourceCodes.get(pos);
            libraryLimit = 40;
            fill.run();
        });
    }

    private List<JSONObject> libraryCards() {
        List<JSONObject> result = new ArrayList<>();
        String needle = librarySearch.toLowerCase(Locale.ROOT);
        for (JSONObject card : store.list("card")) {
            if (!libraryDeck.isEmpty() && !libraryDeck.equals(card.optString("deck_uuid")))
                continue;
            if (favoritesOnly && card.optInt("is_favorite") != 1)
                continue;
            if (!libraryStatus.isEmpty() && !libraryStatus.equals(card.optString("status")))
                continue;
            String code = languageCodes.getOrDefault(
                    card.optString("source_lang", "en"), card.optString("source_lang", "en"));
            if (!libraryLanguage.isEmpty() && !libraryLanguage.equals(code))
                continue;
            if (!(card.optString("term") + " " + card.optString("definition"))
                            .toLowerCase(Locale.ROOT)
                            .contains(needle))
                continue;
            result.add(card);
        }
        return result;
    }

    private void decks() {
        title(t("Your decks"));
        hint(t("Organize words by topic and language."));
        EditText name = field(content, t("New deck name"), "", false);
        EditText description = field(content, t("Description (optional)"), "", false);
        addButton(t("Create deck"), true, () -> {
            if (name.getText().toString().trim().isEmpty()) {
                name.setError(t("Deck name is required"));
                return;
            }
            store.createDeck(name.getText().toString(), description.getText().toString());
            render();
            syncSoon();
        });
        List<JSONObject> cards = store.list("card");
        for (JSONObject deck : store.list("deck")) {
            String id = deck.optString("uuid");
            int count = 0, dueCount = 0;
            for (JSONObject card : cards)
                if (id.equals(card.optString("deck_uuid"))) {
                    count++;
                    if (due(card))
                        dueCount++;
                }
            LinearLayout p = panel();
            p.addView(text(deck.optString("name"), 21, INK));
            p.addView(text(t("{count} words · {due} reviews", "count", count, "due", dueCount), 14,
                    GREEN));
            if (!deck.optString("description").isEmpty())
                p.addView(text(deck.optString("description"), 14, MUTED));
            p.addView(button(t("Study this deck"), true, () -> {
                studyDeck = id;
                studyStarted = false;
                navigate(0);
            }));
            p.addView(button(t("Edit"), false, () -> {
                LinearLayout fields = column();
                fields.setPadding(dp(20), 0, dp(20), 0);
                EditText n = field(fields, t("Deck name"), deck.optString("name"), false);
                EditText d = field(fields, t("Description"), deck.optString("description"), true);
                AlertDialog dialog = new AlertDialog.Builder(this)
                                             .setTitle(t("Edit deck"))
                                             .setView(fields)
                                             .setNegativeButton(t("Cancel"), null)
                                             .setPositiveButton(t("Save"), null)
                                             .create();
                dialog.show();
                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                    if (n.getText().toString().trim().isEmpty()) {
                        n.setError(t("Deck name is required"));
                        return;
                    }
                    CardStore.put(deck, "name", n.getText().toString().trim());
                    CardStore.put(deck, "description", d.getText().toString().trim());
                    store.save("deck", id, deck);
                    dialog.dismiss();
                    render();
                    syncSoon();
                });
            }));
            p.addView(button(t("Delete deck"), false,
                    ()
                            -> new AlertDialog.Builder(this)
                                    .setTitle(t("Delete this deck?"))
                                    .setMessage(t(
                                            "This deck and all its cards will be deleted from this device."))
                                    .setNegativeButton(t("Cancel"), null)
                                    .setPositiveButton(t("Delete"),
                                            (d, w) -> {
                                                store.delete(id);
                                                if (id.equals(studyDeck)) {
                                                    studyDeck = "";
                                                    studyStarted = false;
                                                }
                                                if (id.equals(libraryDeck))
                                                    libraryDeck = "";
                                                render();
                                                syncSoon();
                                            })
                                    .show()));
            content.addView(p);
        }
    }

    private void account() {
        extras.settings();
    }

    void backupButtons() {
        addButton(t("Export to device"), true, () -> {
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            intent.setType("application/json");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.putExtra(Intent.EXTRA_TITLE, "studycard-android-" + LocalDate.now() + ".json");
            startActivityForResult(intent, 103);
        });
        addButton(t("Load device backup"), false, () -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.setType("*/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(intent, 104);
        });
        addButton(t("Export for desktop (.studycard)"), false, () -> {
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            intent.setType("application/octet-stream");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.putExtra(Intent.EXTRA_TITLE, "studycard-" + LocalDate.now() + ".studycard");
            startActivityForResult(intent, 105);
        });
    }

    private String transferFormat = "json", transferDeck = "", practiceKind = "writing";
    private String[] currentChoices = new String[0];
    private String moduleSearch = "", libraryStatus = "", libraryLanguage = "";
    private int modulePage = 0, libraryLimit = 40;
    private final Map<String, List<JSONObject>> moduleCache = new LinkedHashMap<>();
    private int practiceIndex = 0, practiceScore = 0;
    private boolean practiceLocked = false, practicePreparing = false;
    private final ArrayList<JSONObject> practiceCards = new ArrayList<>();
    private void transfer() {
        title(t("Import / export"));
        hint(t("CSV / JSON keeps decks, both languages, usage examples, pronunciation, notes, favorites and review progress. Repeated words are skipped regardless of case."));
        backupButtons();
        List<JSONObject> decks = store.list("deck");
        if (decks.isEmpty()) {
            hint(t("Create a deck first."));
            return;
        }
        Spinner deck = spinner(deckNames(decks, false),
                deckName(transferDeck.isEmpty() ? decks.get(0).optString("uuid") : transferDeck));
        content.addView(deck);
        transferDeck = decks.get(deck.getSelectedItemPosition()).optString("uuid");
        selection(deck, pos -> transferDeck = decks.get(pos).optString("uuid"));
        for (String format : new String[] {"json", "csv"}) {
            addButton(
                    t("Export {format}", "format", format.toUpperCase(Locale.ROOT)), false, () -> {
                        transferFormat = format;
                        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                        intent.setType(format.equals("csv") ? "text/csv" : "application/json");
                        intent.addCategory(Intent.CATEGORY_OPENABLE);
                        intent.putExtra(Intent.EXTRA_TITLE, "studycard." + format);
                        startActivityForResult(intent, 101);
                    });
            addButton(t("Import {format}", "format", format.toUpperCase(Locale.ROOT)), true, () -> {
                transferFormat = format;
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.setType("*/*");
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                startActivityForResult(intent, 102);
            });
        }
    }
    @Override
    protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (result != RESULT_OK || data == null || data.getData() == null)
            return;
        Uri uri = data.getData();
        String format = transferFormat, deck = transferDeck;
        if (request == 103) {
            studio.capture();
            studio.saveTable(false);
            runTask(() -> {
                String value = store.deviceBackup().toString();
                try (java.io.OutputStream out = getContentResolver().openOutputStream(uri, "wt")) {
                    if (out == null)
                        throw new java.io.IOException();
                    out.write(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                }
                return false;
            }, t("Saved"), false);
            return;
        }
        if (request == 104) {
            loadAndroidBackup(uri);
            return;
        }
        if (request == 105) {
            studio.capture();
            studio.saveTable(false);
            runTask(() -> {
                try (java.io.OutputStream out = getContentResolver().openOutputStream(uri, "wt")) {
                    if (out == null)
                        throw new java.io.IOException();
                    DesktopBackup.write(this, store, out);
                }
                return false;
            }, t("Saved"), true);
            return;
        }
        if (request != 101 && request != 102)
            return;
        worker.execute(() -> {
            String message;
            try {
                if (request == 101) {
                    String value = CardTransfer.export(store, format.equals("csv"));
                    try (java.io.OutputStream out =
                                    getContentResolver().openOutputStream(uri, "wt")) {
                        if (out == null)
                            throw new Exception();
                        out.write(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    }
                    message = t("Saved");
                } else {
                    String value;
                    try (InputStream in = getContentResolver().openInputStream(uri)) {
                        if (in == null)
                            throw new Exception();
                        value = SentenceExamples.read(in);
                    }
                    int[] report = CardTransfer.importData(store, value, deck, format.equals("csv"),
                            new LinkedHashMap<>(languageCodes));
                    message = t("Added: {added} · Already exists: {skipped} · Invalid: {invalid}",
                            "added", report[0], "skipped", report[1], "invalid", report[2]);
                }
            } catch (Exception error) {
                message = t("Unable to read the file: {error}", "error",
                        t(error.getMessage() == null ? "Unsupported card backup."
                                                     : error.getMessage()));
            }
            final String status = message;
            handler.post(() -> {
                if (!isDestroyed()) {
                    toast(status);
                    render();
                    if (request == 102)
                        syncSoon();
                }
            });
        });
    }

    private void loadAndroidBackup(Uri uri) {
        if (busy)
            return;
        studio.capture();
        studio.saveTable(false);
        studio.pause();
        busy = true;
        exampleGeneration++;
        practiceGeneration++;
        speech.stop();
        syncStatus.setText(t("Preparing backup…"));
        worker.execute(() -> {
            try {
                JSONObject backup;
                try (InputStream original = getContentResolver().openInputStream(uri)) {
                    if (original == null)
                        throw new java.io.IOException();
                    java.io.BufferedInputStream in = new java.io.BufferedInputStream(original);
                    in.mark(4);
                    int first = in.read(), second = in.read();
                    in.reset();
                    if (first == 'P' && second == 'K')
                        backup = DesktopBackup.read(this, in);
                    else {
                        ByteArrayOutputStream out = new ByteArrayOutputStream();
                        byte[] buffer = new byte[8192];
                        int count;
                        while ((count = in.read(buffer)) != -1) {
                            out.write(buffer, 0, count);
                            if (out.size() > 64 * 1024 * 1024)
                                throw new java.io.IOException("Backup is too large");
                        }
                        backup = new JSONObject(out.toString("UTF-8"));
                    }
                }
                store.validateDeviceBackup(backup);
                int cards = 0, decks = 0;
                JSONArray items = backup.getJSONObject("tables").getJSONArray("items");
                for (int i = 0; i < items.length(); i++) {
                    JSONObject item = items.getJSONObject(i);
                    if (item.optInt("deleted") == 0) {
                        if (item.optString("entity").equals("card"))
                            cards++;
                        if (item.optString("entity").equals("deck"))
                            decks++;
                    }
                }
                final int cardCount = cards, deckCount = decks;
                handler.post(() -> {
                    busy = false;
                    if (isDestroyed())
                        return;
                    new AlertDialog.Builder(this)
                            .setTitle(t("Load device backup"))
                            .setMessage(t(
                                    "This backup contains {cards} cards and {decks} decks. Loading replaces your current library and history. A recovery copy of your current data is saved first. Continue?",
                                    "cards", cardCount, "decks", deckCount))
                            .setNegativeButton(t("Cancel"), null)
                            .setPositiveButton(t("Load device backup"),
                                    (dialog, which)
                                            -> runTask(
                                                    ()
                                                            -> {
                                                        java.io.File directory = new java.io.File(
                                                                getFilesDir(), "backups");
                                                        if (!directory.exists()
                                                                && !directory.mkdirs())
                                                            throw new java.io.IOException();
                                                        java.io.File recovery = new java.io.File(
                                                                directory,
                                                                "before-restore-"
                                                                        + System.currentTimeMillis()
                                                                        + ".json");
                                                        try (java.io.FileOutputStream out = new java
                                                                        .io.FileOutputStream(
                                                                                recovery)) {
                                                            out.write(store.deviceBackup()
                                                                            .toString()
                                                                            .getBytes(
                                                                                    java.nio.charset
                                                                                            .StandardCharsets
                                                                                            .UTF_8));
                                                        }
                                                        store.restoreDeviceBackup(backup);
                                                        handler.post(() -> {
                                                            studyStarted = false;
                                                            queue.clear();
                                                            studyIndex = 0;
                                                            practiceCards.clear();
                                                            practiceIndex = 0;
                                                            draft = null;
                                                            editing = "";
                                                            originalCard = null;
                                                            uiLanguage = store.config(
                                                                    "ui_language", "tr");
                                                            locale = new L10n(this, uiLanguage);
                                                            studio.reset();
                                                            languageNames.clear();
                                                            languageCodes.clear();
                                                            loadLanguages();
                                                            applyPreferences();
                                                            MobileReminders.schedule(this, store);
                                                            MobileReminders.scheduleTimer(
                                                                    this, store);
                                                            StudyWidget.refresh(this);
                                                            page = 4;
                                                            buildRoot();
                                                            render();
                                                        });
                                                        return false;
                                                    },
                                                    t("Saved"), true))
                            .show();
                });
            } catch (Exception error) {
                handler.post(() -> {
                    busy = false;
                    if (!isDestroyed())
                        syncStatus.setText(
                                t("Backup failed: {error}", "error", error.getMessage()));
                });
            }
        });
    }
    private List<JSONObject> module(String id) {
        if (moduleCache.containsKey(id))
            return moduleCache.get(id);
        List<JSONObject> result = new ArrayList<>();
        try (InputStream in = getAssets().open(id + ".json")) {
            JSONArray rows = new JSONArray(SentenceExamples.read(in));
            for (int i = 0; i < rows.length(); i++) result.add(rows.getJSONObject(i));
        } catch (Exception ignored) {
        }
        moduleCache.put(id, result);
        return result;
    }
    void beginPractice(String kind, List<JSONObject> cards) {
        if (busy)
            return;
        captureDraft();
        studio.pause();
        speech.stop();
        practiceKind = kind;
        practiceCards.clear();
        practiceIndex = practiceScore = 0;
        practiceLocked = false;
        practicePreparing = true;
        page = 7;
        render();
        int ticket = ++practiceGeneration;
        List<JSONObject> source = new ArrayList<>();
        for (JSONObject card : cards) source.add(CardStore.json(card.toString()));
        worker.execute(() -> {
            List<JSONObject> prepared = new ArrayList<>();
            for (JSONObject card : source) {
                if (ticket != practiceGeneration || Thread.currentThread().isInterrupted())
                    return;
                if (kind.equals("shadowing") || kind.equals("cloze")) {
                    String sentence = usageSentence(card);
                    if (sentence.isEmpty())
                        continue;
                    CardStore.put(card, "example_sentence", sentence);
                }
                prepared.add(card);
            }
            if (store.flag("shuffle_cards", true))
                Collections.shuffle(prepared);
            int count = Math.max(5, Math.min(200, store.number("session_size", 50)));
            if (prepared.size() > count)
                prepared.subList(count, prepared.size()).clear();
            handler.post(() -> {
                if (ticket != practiceGeneration || page != 7 || isDestroyed())
                    return;
                practiceCards.addAll(prepared);
                practicePreparing = false;
                render();
            });
        });
    }
    static final String[] CORE_ROUTES = {"study", "add", "library", "decks", "maker", "timer",
            "stats", "import", "match", "sentence_memory", "writing", "mistakes", "favorites",
            "shadowing", "dictation", "cloze", "settings"};
    static final String[] CORE_NAMES = {"Study", "New word", "Your words", "Your decks",
            "Create extension", "Timer", "Statistics", "Import / export", "Speed Match",
            "Sentence Memory", "Written Recall", "My Mistakes", "Favorites", "Shadowing",
            "Listening", "Fill in the Blank", "Settings"};
    static final String[] MODULE_IDS = {"en_phrasal", "en_confusing_words", "en_verbs",
            "de_articles", "fr_verbs", "es_verbs", "it_verbs", "pt_verbs", "nl_articles",
            "sv_articles", "zh_words", "ja_words", "ko_words", "ru_words", "tr_words", "ar_words",
            "hi_words"};
    private void extensions() {
        title(t("Extensions"));
        hint(t("Choose what appears in your menu. Hidden extensions can still be opened here."));
        addButton(t("Show all in menu"), false, () -> {
            Map<String, String> values = new LinkedHashMap<>();
            for (String route : CORE_ROUTES) values.put("menu_visible_" + route, "true");
            for (String route : MODULE_IDS) values.put("plugin_" + route, "true");
            for (String kind : new String[] {"table", "game"})
                for (JSONObject doc : store.list(kind))
                    values.put(StudioData.menuKey(kind, doc.optString("id")), "true");
            store.configUpdate(values);
            render();
        });
        hint(t("MY EXTENSIONS"));
        for (String kind : new String[] {"table", "game"})
            for (JSONObject doc : store.list(kind)) {
                LinearLayout p = panel();
                p.addView(text(doc.optString("name"), 21, INK));
                if (!doc.optString("description").isEmpty())
                    p.addView(text(doc.optString("description"), 14, MUTED));
                String route = kind + ":" + doc.optString("id");
                extensionActions(p, StudioData.menuKey(kind, doc.optString("id")), false, route,
                        doc.optString("icon"));
                if (kind.equals("game"))
                    p.addView(button(t("Edit"), false, () -> studio.newGame(doc)));
                content.addView(p);
            }
        hint(t("CORE APPLICATION MENUS"));
        for (int i = 0; i < CORE_ROUTES.length; i++) {
            LinearLayout p = panel();
            p.addView(text(t(CORE_NAMES[i]), 20, INK));
            extensionActions(
                    p, "menu_visible_" + CORE_ROUTES[i], true, CORE_ROUTES[i], CORE_ROUTES[i]);
            content.addView(p);
        }
        hint(t("LANGUAGE & PRACTICE EXTENSIONS"));
        for (String id : MODULE_IDS) {
            LinearLayout p = panel();
            p.addView(text(t("module_" + id), 20, INK));
            extensionActions(p, "plugin_" + id, false, id, "globe");
            content.addView(p);
        }
    }
    private void extensionActions(
            LinearLayout panel, String key, boolean defaultValue, String route, String symbol) {
        boolean active = store.flag(key, defaultValue);
        Button toggle = button(t(active ? "Active in menu" : "Add to menu"), false, () -> {
            store.configSet(key, Boolean.toString(!active));
            render();
        });
        if (active) {
            toggle.setBackground(background(Color.rgb(21, 59, 54), 12));
            toggle.setTextColor(Color.rgb(110, 231, 183));
        }
        panel.addView(toggle);
        Button open = button(
                t(route.startsWith("game:") ? "Play" : "Open"), true, () -> openRoute(route));
        icon(open, symbol);
        panel.addView(open);
    }
    private void showMenu() {
        final Dialog[] popup = new Dialog[1];
        popup[0] = new StudioUi(this).dialog("Menu", box -> {
            for (int i = 0; i < CORE_ROUTES.length; i++)
                if (store.flag("menu_visible_" + CORE_ROUTES[i], true)) {
                    String route = CORE_ROUTES[i];
                    Button b = button(t(CORE_NAMES[i]), false, () -> {
                        popup[0].dismiss();
                        openRoute(route);
                    });
                    icon(b, route);
                    box.addView(b);
                }
            for (String kind : new String[] {"table", "game"})
                for (JSONObject doc : store.list(kind))
                    if (store.flag(StudioData.menuKey(kind, doc.optString("id")), false)) {
                        Button b = button(doc.optString("name"), false, () -> {
                            popup[0].dismiss();
                            openRoute(kind + ":" + doc.optString("id"));
                        });
                        icon(b, doc.optString("icon"));
                        box.addView(b);
                    }
            for (String id : MODULE_IDS)
                if (store.flag("plugin_" + id, false))
                    box.addView(button(t("module_" + id), false, () -> {
                        popup[0].dismiss();
                        openRoute(id);
                    }));
            Button extensions = button(t("Extensions"), true, () -> {
                popup[0].dismiss();
                navigate(6);
            });
            icon(extensions, "extensions");
            box.addView(extensions);
            if (!store.flag("menu_visible_settings", true))
                box.addView(button(t("Settings"), false, () -> {
                    popup[0].dismiss();
                    navigate(4);
                }));
        }, null, null);
    }
    void openRoute(String route) {
        if (route == null || busy)
            return;
        switch (route) {
            case "study":
                navigate(0);
                return;
            case "add":
                navigate(1);
                return;
            case "library":
                navigate(2);
                return;
            case "decks":
                navigate(3);
                return;
            case "settings":
                navigate(4);
                return;
            case "import":
                navigate(5);
                return;
            case "extensions":
                navigate(6);
                return;
            case "maker":
            case "tables":
                navigate(9);
                return;
            case "stats":
                navigate(13);
                return;
            case "timer":
                navigate(14);
                return;
            case "sentence_memory":
                navigate(15);
                return;
            case "favorites":
                navigate(17);
                return;
            case "mistakes":
                navigate(18);
                return;
            case "match":
                extras.beginLibraryGame("matching", store.list("card"));
                return;
            case "writing":
            case "dictation":
            case "shadowing":
            case "cloze":
                beginPractice(route, store.list("card"));
                return;
        }
        if (route.startsWith("table:")) {
            studio.openTable(route.substring(6));
            return;
        }
        if (route.startsWith("game:")) {
            JSONObject game = store.get(route.substring(5));
            if (game == null) {
                toast("This extension is no longer available.");
                return;
            }
            studio.startGame(game, false);
            return;
        }
        if (Arrays.asList(MODULE_IDS).contains(route))
            openModule(route);
    }
    private void openModule(String id) {
        practiceKind = id;
        moduleSearch = "";
        modulePage = 0;
        navigate(8);
    }
    private void moduleTable() {
        title(t("module_" + practiceKind));
        List<JSONObject> rows = module(practiceKind);
        EditText search = field(content, t("Search word or meaning"), moduleSearch, false);
        List<JSONObject> visible = new ArrayList<>();
        String needle = moduleSearch.toLowerCase(Locale.ROOT);
        for (JSONObject item : rows) {
            JSONObject translations = item.optJSONObject("translations");
            if ((item.optString("term") + " " + item.optString("attr") + " "
                        + item.optString("extra") + " "
                        + (translations == null ? "" : translations.optString(uiLanguage)))
                            .toLowerCase(Locale.ROOT)
                            .contains(needle))
                visible.add(item);
        }
        addButton(t("Practice Quiz"), true, () -> {
            if (practiceKind.equals("en_confusing_words")) {
                beginPractice(practiceKind, visible);
                return;
            }
            List<JSONObject> cards = new ArrayList<>();
            for (JSONObject item : visible) {
                JSONObject card = new JSONObject();
                CardStore.put(card, "term", item.optString("term"));
                CardStore.put(card, "definition",
                        item.optJSONObject("translations")
                                .optString(uiLanguage, item.optString("term")));
                CardStore.put(card, "source_lang", practiceKind.substring(0, 2));
                CardStore.put(card, "target_lang", uiLanguage);
                cards.add(card);
            }
            extras.beginLibraryGame("quiz", cards);
        });
        addButton(t("Create editable table from module"), false,
                () -> new StudioUi(this).rename("Table name", t("module_" + practiceKind), name -> {
                    JSONObject table = StudioData.table(name, "blank", 0, 4);
                    String[] labels = {t("Word"), t("Form / context"),
                            t("Additional form / example"), t("Meaning")};
                    JSONArray cols = table.optJSONArray("columns");
                    for (int i = 0; i < 4; i++) {
                        JSONObject col = cols.optJSONObject(i);
                        CardStore.put(col, "name", labels[i]);
                        CardStore.put(col, "language",
                                i == 3 ? uiLanguage : practiceKind.substring(0, 2));
                        CardStore.put(col, "speech_order", i == 3 ? 0 : i + 1);
                    }
                    for (JSONObject item : rows) {
                        JSONObject row = StudioData.row(
                                Integer.toString(table.optJSONArray("rows").length() + 1));
                        String[] values = {item.optString("term"), item.optString("attr"),
                                item.optString("extra"),
                                item.optJSONObject("translations").optString(uiLanguage)};
                        for (int i = 0; i < 4; i++)
                            CardStore.put(row.optJSONObject("cells"),
                                    cols.optJSONObject(i).optString("id"), values[i]);
                        table.optJSONArray("rows").put(row);
                    }
                    StudioData.save(store, "table", table);
                    studio.openTable(table.optString("id"));
                }));
        LinearLayout area = column();
        content.addView(area);
        renderModuleRows(visible, area);
        search.addTextChangedListener(MobileStudio.watch(() -> {
            moduleSearch = search.getText().toString();
            modulePage = 0;
            visible.clear();
            String query = moduleSearch.toLowerCase(Locale.ROOT);
            for (JSONObject item : rows) {
                JSONObject translations = item.optJSONObject("translations");
                if ((item.optString("term") + " " + item.optString("attr") + " "
                            + item.optString("extra") + " "
                            + (translations == null ? "" : translations.optString(uiLanguage)))
                                .toLowerCase(Locale.ROOT)
                                .contains(query))
                    visible.add(item);
            }
            renderModuleRows(visible, area);
        }));
    }
    private void renderModuleRows(List<JSONObject> visible, LinearLayout area) {
        area.removeAllViews();
        int total = visible.size();
        modulePage = Math.max(0, Math.min(modulePage, Math.max(0, (total - 1) / 20)));
        area.addView(text(
                t("Rows {start}–{end} of {total}", "start", total == 0 ? 0 : modulePage * 20 + 1,
                        "end", Math.min(total, (modulePage + 1) * 20), "total", total),
                14, MUTED));
        for (int i = modulePage * 20; i < Math.min(total, (modulePage + 1) * 20); i++) {
            JSONObject item = visible.get(i);
            LinearLayout p = panel();
            String word = item.optString("term"), partner = item.optString("confused_with");
            p.addView(text(word + (partner.isEmpty() ? "" : " / " + partner), 22, INK));
            if (!item.optString("attr").isEmpty())
                p.addView(text(item.optString("attr"), 18, GREEN));
            if (!item.optString("extra").isEmpty()
                    && !item.optString("extra").equals(item.optString("example")))
                p.addView(text(item.optString("extra"), 16, INK));
            JSONObject translations = item.optJSONObject("translations");
            if (translations != null)
                p.addView(text(translations.optString(uiLanguage, word), 16, GREEN));
            if (!item.optString("example").isEmpty())
                p.addView(text(item.optString("example"), 15, MUTED));
            JSONObject spoken = CardStore.json(item.toString());
            CardStore.put(spoken, "source_lang", practiceKind.substring(0, 2));
            p.addView(button(t("Listen"), false, () -> speak(spoken)));
            if (!item.optString("example").isEmpty())
                p.addView(button(t("Listen to sentence"), false,
                        ()
                                -> speech.play(item.optString("example"),
                                        practiceKind.substring(0, 2), this::toast)));
            p.addView(button(t("Add to my deck"), false, () -> addModuleCard(item)));
            area.addView(p);
        }
        LinearLayout pagination = row();
        Button previous = button(t("Previous"), false, () -> {
            modulePage--;
            renderModuleRows(visible, area);
        });
        previous.setEnabled(modulePage > 0);
        Button next = button(t("Next"), false, () -> {
            modulePage++;
            renderModuleRows(visible, area);
        });
        next.setEnabled((modulePage + 1) * 20 < total);
        pagination.addView(previous, new LinearLayout.LayoutParams(0, dp(52), 1));
        pagination.addView(next, new LinearLayout.LayoutParams(0, dp(52), 1));
        area.addView(pagination);
    }
    private void addModuleCard(JSONObject item) {
        List<JSONObject> decks = store.list("deck");
        if (decks.isEmpty()) {
            toast("Create a deck first.");
            return;
        }
        final Spinner[] choice = new Spinner[1];
        new StudioUi(this).dialog("Add to my deck",
                box
                -> {
                    choice[0] = spinner(deckNames(decks, false), deckNames(decks, false).get(0));
                    box.addView(choice[0]);
                },
                "Save",
                () -> {
                    JSONObject card = newCard();
                    CardStore.put(card, "term", item.optString("term"));
                    CardStore.put(card, "definition",
                            item.optJSONObject("translations").optString(uiLanguage));
                    CardStore.put(card, "source_lang", practiceKind.substring(0, 2));
                    CardStore.put(card, "target_lang", uiLanguage);
                    CardStore.put(card, "example_sentence", item.optString("example"));
                    CardStore.put(card, "deck_uuid",
                            decks.get(choice[0].getSelectedItemPosition()).optString("uuid"));
                    if (!store.duplicates(card.optString("term"), "").isEmpty()) {
                        toast("Word already exists");
                        return false;
                    }
                    store.save("card", null, card);
                    toast("Saved");
                    StudyWidget.refresh(this);
                    return true;
                });
    }
    private String practiceTitle(String kind) {
        switch (kind) {
            case "dictation":
                return "Listening";
            case "cloze":
                return "Fill in the Blank";
            case "shadowing":
                return "Shadowing";
            case "en_confusing_words":
                return "Commonly Confused Words";
            case "en_phrasal":
                return "Phrasal Verbs: Everyday Use";
            default:
                return "Written Recall";
        }
    }
    private void practice() {
        if (practicePreparing) {
            title(t("Preparing practice…"));
            hint(t("You can keep using the menu while sentences load."));
            return;
        }
        title(t(practiceKind.contains("_") ? "module_" + practiceKind
                                           : practiceTitle(practiceKind)));
        boolean contextual = practiceKind.equals("cloze") || practiceKind.equals("shadowing");
        while (practiceIndex < practiceCards.size() && contextual) {
            JSONObject candidate = practiceCards.get(practiceIndex);
            String usage = usageSentence(candidate);
            if (!usage.isEmpty()) {
                CardStore.put(candidate, "example_sentence", usage);
                break;
            }
            practiceIndex++;
        }
        if (practiceIndex >= practiceCards.size()) {
            hint(t(practiceCards.isEmpty() ? t("No cards yet") : t("Session complete.")));
            hint(t("No contextual examples yet. Add a full usage sentence or connect to search."));
            addButton(t("Restart"), false, () -> navigate(6));
            return;
        }
        final int generation = ++practiceGeneration;
        practiceLocked = false;
        JSONObject card = practiceCards.get(practiceIndex);
        String term = card.optString("term"),
               sentence = card.optString("example_sentence", card.optString("example"));
        boolean paired = practiceKind.equals("en_confusing_words"),
                module = card.has("translations"), shadow = practiceKind.equals("shadowing"),
                listening = practiceKind.equals("dictation");
        String expected = module && !paired
                ? card.optJSONObject("translations").optString(uiLanguage, term)
                : term;
        String question = paired
                ? SentenceExamples.pattern(term, "en").matcher(sentence).replaceAll("____")
                : practiceKind.equals("cloze")
                ? SentenceExamples.pattern(term, card.optString("source_lang", "en"))
                          .matcher(sentence)
                          .replaceAll("____")
                : shadow    ? sentence
                : listening ? "♪"
                : module    ? term
                            : card.optString("definition");
        hint(t("Correct: {score}", "score", practiceScore));
        content.addView(text(question, 23, INK));
        JSONObject spoken = CardStore.json(card.toString());
        if (shadow || practiceKind.equals("cloze"))
            CardStore.put(spoken, "term", sentence);
        if (module)
            CardStore.put(spoken, "source_lang", practiceKind.substring(0, 2));
        addButton(t("Listen"), false, () -> speak(spoken));
        TextView feedback = text("", 16, GREEN);
        content.addView(feedback);
        Button next = button(t("Next Question"), false, () -> {
            practiceIndex++;
            render();
        });
        next.setVisibility(View.GONE);
        content.addView(next);
        java.util.function.Consumer<String> check = answer -> {
            if (practiceLocked || answer.trim().isEmpty())
                return;
            practiceLocked = true;
            boolean correct = GameEngine
                                      .normalize(answer,
                                              languageCodes.getOrDefault(
                                                      card.optString("source_lang", "en"), "en"))
                                      .equals(GameEngine.normalize(expected,
                                              languageCodes.getOrDefault(
                                                      card.optString("source_lang", "en"), "en")));
            if (correct)
                practiceScore++;
            if (!card.optString("uuid").isEmpty())
                store.recordPractice(
                        card.optString("uuid"), practiceKind, answer, expected, correct);
            extras.sound(correct);
            feedback.setText(t(
                    correct ? "Correct!" : "Wrong! Correct answer: {answer}", "answer", expected));
            feedback.setTextColor(correct ? GREEN : Color.rgb(251, 113, 133));
            next.setVisibility(View.VISIBLE);
            next.setEnabled(true);
            if (correct && store.flag("practice_auto_next", true)) {
                int index = practiceIndex;
                handler.postDelayed(() -> {
                    if (page == 7 && practiceLocked && practiceIndex == index
                            && practiceGeneration == generation) {
                        practiceIndex++;
                        render();
                    }
                }, store.number("practice_advance_ms", 300));
            }
        };
        if (paired) {
            currentChoices = new String[] {term, card.optString("confused_with")};
            if (Math.random() < .5) {
                String swap = currentChoices[0];
                currentChoices[0] = currentChoices[1];
                currentChoices[1] = swap;
            }
            for (String choice : currentChoices)
                addButton(choice, true, () -> check.accept(choice));
            hint(t("Choose the word that fits this sentence."));
        } else if (shadow)
            addButton(t("Repeated Aloud"), true, () -> check.accept(expected));
        else {
            EditText answer = field(content, t("Your answer"), "", false);
            answer.setInputType(InputType.TYPE_CLASS_TEXT);
            addButton(t("Check"), true, () -> check.accept(answer.getText().toString()));
            answer.setOnEditorActionListener((v, action, event) -> {
                check.accept(answer.getText().toString());
                return true;
            });
        }
        if (store.flag("audio_prefetch", true))
            for (int i = practiceIndex + 1; i < Math.min(practiceCards.size(), practiceIndex + 3);
                    i++) {
                JSONObject upcoming = practiceCards.get(i);
                handler.postDelayed(() -> {
                    if (page == 7)
                        prefetchPractice(upcoming);
                }, 400);
            }
        if (store.flag("practice_autoplay", true) && (listening || shadow))
            handler.post(() -> {
                if (page == 7 && !practiceLocked && practiceGeneration == generation)
                    speak(spoken);
            });
    }

    interface Task {
        boolean run() throws Exception;
    }
    private void runTask(Task task, String success, boolean refreshAccount) {
        if (busy)
            return;
        busy = true;
        syncStatus.setText(t("Working…"));
        worker.execute(() -> {
            boolean changed = false;
            String error = null;
            try {
                changed = task.run();
            } catch (Exception e) {
                error = e.getMessage() == null ? "İşlem tamamlanamadı; yeniden dene."
                                               : e.getMessage();
            }
            final boolean updated = changed;
            final String message = error;
            handler.post(() -> {
                busy = false;
                if (isFinishing() || isDestroyed())
                    return;
                syncStatus.setText(
                        message != null ? t(message) : t("Offline · words on this device"));
                if (message != null && refreshAccount)
                    toast(message);
                if (message == null && !success.isEmpty())
                    toast(success);
                if ((refreshAccount && page == 4) || (updated && (page == 2 || page == 3)))
                    render();
            });
        });
    }
    private void syncSoon() {}
    private final Runnable syncDebounce = () -> syncNow(false);
    private void syncNow(boolean feedback) {}
}
