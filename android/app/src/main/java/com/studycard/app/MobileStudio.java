package com.studycard.app;

import android.app.Dialog;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Color;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

/** Native mobile extension hub, table editor, designer and eight playable game modes. */
final class MobileStudio {
    final MainActivity a;
    final StudioUi ui;
    JSONObject table, gameDraft, playing;
    Runnable captureAction;
    int tablePage, columnPage;
    GameEngine session;
    boolean preview, recorded, active, audioReady = true;
    int playerGeneration, remaining;
    long elapsed, startTime, lastTick;
    TextView feedback, clock;
    String feedbackText = "";
    final Runnable tableSave = () -> saveTable(false);
    final Runnable ticker = new Runnable() {
        public void run() {
            tick();
            if (active && session != null && !session.complete())
                a.handler.postDelayed(this, 100);
        }
    };
    MobileStudio(MainActivity activity) {
        a = activity;
        ui = new StudioUi(a);
    }
    void capture() {
        if (captureAction != null)
            captureAction.run();
    }
    void pause() {
        capture();
        if (active) {
            elapsed += Math.max(0, android.os.SystemClock.elapsedRealtime() - startTime);
            active = false;
        }
        a.handler.removeCallbacks(ticker);
        playerGeneration++;
    }
    void resume() {
        if (a.page == 12 && session != null && !session.complete()) {
            active = true;
            startTime = lastTick = android.os.SystemClock.elapsedRealtime();
            a.handler.removeCallbacks(ticker);
            a.handler.post(ticker);
            if (GameEngine.audio(session.mode) && !session.locked)
                listenQuestion();
        }
    }
    void saveTable(boolean notify) {
        a.handler.removeCallbacks(tableSave);
        if (table != null && !a.busy) {
            StudioData.save(a.store, "table", table);
            if (notify)
                a.toast("Saved");
        }
    }
    void changed() {
        a.handler.removeCallbacks(tableSave);
        a.handler.postDelayed(tableSave, 400);
    }
    void home() {
        captureAction = null;
        a.title(a.t("Create extension"));
        a.hint(a.t("Build your own tables and games. Choose what appears in your menu."));
        Button create = a.button(a.t("New table"), true, this::newTable);
        a.icon(create, "table_grid");
        a.content.addView(create);
        Button design = a.button(a.t("Design a game"), false, () -> newGame(null));
        a.icon(design, "gamepad");
        a.content.addView(design);
        if (gameDraft != null)
            a.addButton(a.t("Continue game draft"), false, () -> a.navigate(11));
        a.addButton(a.t("Extensions"), false, () -> a.navigate(6));
        for (String kind : new String[] {"table", "game"})
            for (JSONObject value : a.store.list(kind)) {
                LinearLayout card = a.panel();
                card.addView(a.text(value.optString("name"), 21, a.INK));
                if (!value.optString("description").isEmpty())
                    card.addView(a.text(value.optString("description"), 14, a.MUTED));
                Button open = a.button(a.t(kind.equals("table") ? "Open" : "Play"), true, () -> {
                    if (kind.equals("table"))
                        openTable(value.optString("id"));
                    else
                        startGame(value, false);
                });
                a.icon(open, value.optString("icon"));
                card.addView(open);
                if (kind.equals("game"))
                    card.addView(a.button(a.t("Edit"), false, () -> newGame(value)));
                a.content.addView(card);
            }
    }
    void newTable() {
        final EditText[] name = new EditText[1], description = new EditText[1],
                         rows = new EditText[1], cols = new EditText[1];
        final Spinner[] template = new Spinner[1];
        final String[] icon = {"table_grid"};
        ui.dialog("New table",
                box
                -> {
                    box.addView(a.text(
                            a.t("Name your table, choose an icon and start with a template."), 15,
                            a.MUTED));
                    name[0] = a.field(box, a.t("Table name"), "", false);
                    description[0] = a.field(box, a.t("Description"), "", true);
                    box.addView(ui.iconPicker(icon[0], value -> icon[0] = value));
                    template[0] = ui.options(box, "Starting template",
                            new String[] {"Blank table", "Irregular verbs", "Phrases and examples"},
                            new String[] {"blank", "verbs", "phrases"}, "blank");
                    rows[0] = ui.number(box, "Starting rows", 4);
                    cols[0] = ui.number(box, "Starting columns", 2);
                    a.selection(template[0],
                            pos
                            -> cols[0].setText(pos == 1 ? "4"
                                            : pos == 2  ? "3"
                                                        : "2"));
                },
                "Create table",
                () -> {
                    try {
                        String title = name[0].getText().toString().trim();
                        if (title.isEmpty()) {
                            name[0].setError(a.t("Please enter a name."));
                            return false;
                        }
                        table = StudioData.table(title,
                                new String[] {"blank", "verbs",
                                        "phrases"}[template[0].getSelectedItemPosition()],
                                ui.number(rows[0], 1, 100), ui.number(cols[0], 1, 16));
                        for (int i = 0; i < table.optJSONArray("columns").length(); i++) {
                            JSONObject col = table.optJSONArray("columns").optJSONObject(i);
                            CardStore.put(col, "name", a.t(col.optString("name")));
                        }
                        CardStore.put(
                                table, "description", description[0].getText().toString().trim());
                        CardStore.put(table, "icon", icon[0]);
                        saveTable(false);
                        tablePage = columnPage = 0;
                        a.navigate(10);
                        return true;
                    } catch (IllegalArgumentException invalid) {
                        a.toast(invalid.getMessage());
                        return false;
                    }
                });
    }
    void openTable(String id) {
        saveTable(false);
        table = a.store.get(id);
        tablePage = columnPage = 0;
        if (table == null) {
            a.toast("This extension is no longer available.");
            return;
        }
        a.navigate(10);
    }
    void tableEditor() {
        captureAction = null;
        if (table == null) {
            home();
            return;
        }
        a.title(table.optString("name"));
        a.hint(a.t("Rename rows and columns, choose speech order and mute individual cells."));
        a.addButton(a.t("Back to studio"), false, () -> {
            saveTable(false);
            a.navigate(9);
        });
        LinearLayout actions = a.row();
        actions.addView(a.button(a.t("Add row"), true, () -> {
            if (table.optJSONArray("rows").length() >= 10000) {
                a.toast("Invalid table size");
                return;
            }
            table.optJSONArray("rows").put(
                    StudioData.row(Integer.toString(table.optJSONArray("rows").length() + 1)));
            tablePage = (table.optJSONArray("rows").length() - 1) / 20;
            saveTable(false);
            a.render();
        }), new LinearLayout.LayoutParams(0, a.dp(52), 1));
        actions.addView(
                a.button(a.t("Add column"), false, () -> ui.rename("Add column", "", name -> {
                    JSONArray cols = table.optJSONArray("columns");
                    if (cols.length() >= 64) {
                        a.toast("Invalid table size");
                        return;
                    }
                    JSONObject col = new JSONObject();
                    CardStore.put(col, "id", CardStore.uuid());
                    CardStore.put(col, "name", name);
                    CardStore.put(col, "language", "en");
                    CardStore.put(col, "speech_order", cols.length() + 1);
                    cols.put(col);
                    columnPage = (cols.length() - 1) / 8;
                    saveTable(false);
                    a.render();
                })), new LinearLayout.LayoutParams(0, a.dp(52), 1));
        a.content.addView(actions);
        a.addButton(a.t("Table settings"), false, this::tableSettings);
        a.addButton(a.t("Paste spreadsheet cells"), false, this::pasteCells);
        if (table.optBoolean("speakers")) {
            a.addButton(a.t("Read table"), true, () -> readTable(-1));
            a.addButton(a.t("Stop audio"), false, a.speech::stop);
        }
        JSONArray columns = table.optJSONArray("columns"), rows = table.optJSONArray("rows");
        tablePage = Math.max(0, Math.min(tablePage, Math.max(0, (rows.length() - 1) / 20)));
        a.hint(a.t("Rows {start}–{end} of {total}", "start",
                rows.length() == 0 ? 0 : tablePage * 20 + 1, "end",
                Math.min(rows.length(), (tablePage + 1) * 20), "total", rows.length()));
        columnPage = Math.max(0, Math.min(columnPage, (columns.length() - 1) / 8));
        int columnStart = columnPage * 8, columnEnd = Math.min(columns.length(), columnStart + 8);
        if (columns.length() > 8) {
            a.hint(a.t("Columns {start}–{end} of {total}", "start", columnStart + 1, "end",
                    columnEnd, "total", columns.length()));
            LinearLayout navigation = a.row();
            Button earlier = a.button(a.t("Previous columns"), false, () -> {
                saveTable(false);
                columnPage--;
                a.render();
            });
            earlier.setEnabled(columnPage > 0);
            Button later = a.button(a.t("Next columns"), false, () -> {
                saveTable(false);
                columnPage++;
                a.render();
            });
            later.setEnabled(columnEnd < columns.length());
            navigation.addView(earlier, new LinearLayout.LayoutParams(0, a.dp(52), 1));
            navigation.addView(later, new LinearLayout.LayoutParams(0, a.dp(52), 1));
            a.content.addView(navigation);
        }
        HorizontalScrollView horizontal = new HorizontalScrollView(a);
        LinearLayout grid = a.column(), header = a.row();
        header.addView(a.text(a.t("Row"), 16, a.MUTED),
                new LinearLayout.LayoutParams(a.dp(110), a.dp(64)));
        for (int i = columnStart; i < columnEnd; i++) {
            final int index = i;
            JSONObject col = columns.optJSONObject(i);
            Button head = a.button(col.optString("name"), false, () -> columnSettings(index));
            head.setContentDescription(col.optString("name") + " · " + a.t("Column settings"));
            header.addView(head, new LinearLayout.LayoutParams(a.dp(172), a.dp(64)));
        }
        grid.addView(header);
        for (int r = tablePage * 20; r < Math.min(rows.length(), (tablePage + 1) * 20); r++) {
            final int index = r;
            JSONObject row = rows.optJSONObject(r);
            LinearLayout line = a.row(), rowLabel = a.column();
            rowLabel.addView(a.button(row.optString("name"), false, () -> rowSettings(index)));
            if (table.optBoolean("speakers"))
                rowLabel.addView(a.button(a.t("Listen"), false, () -> readTable(index)));
            line.addView(rowLabel, new LinearLayout.LayoutParams(a.dp(110), -2));
            for (int c = columnStart; c < columnEnd; c++) {
                int columnIndex = c;
                JSONObject col = columns.optJSONObject(c);
                String id = col.optString("id");
                LinearLayout cell = a.column();
                cell.setPadding(a.dp(4), a.dp(3), a.dp(4), a.dp(3));
                EditText editor =
                        a.field(cell, "", row.optJSONObject("cells").optString(id), false);
                editor.setInputType(android.text.InputType.TYPE_CLASS_TEXT);
                editor.setContentDescription(row.optString("name") + " · " + col.optString("name"));
                editor.addTextChangedListener(watch(() -> {
                    CardStore.put(row.optJSONObject("cells"), id, editor.getText().toString());
                    changed();
                }));
                if (table.optBoolean("speakers")) {
                    boolean muted = muted(row, id) || col.optInt("speech_order") == 0;
                    Button mute = a.button(a.t(muted ? "Silent" : "Sound on"), false, () -> {
                        if (col.optInt("speech_order") == 0) {
                            columnSettings(columnIndex);
                            return;
                        }
                        toggleMuted(row, id);
                        saveTable(false);
                        a.render();
                    });
                    a.icon(mute, muted ? "microphone" : "audio");
                    cell.addView(mute);
                }
                line.addView(cell, new LinearLayout.LayoutParams(a.dp(172), -2));
            }
            grid.addView(line);
        }
        horizontal.addView(grid);
        a.content.addView(horizontal);
        LinearLayout paging = a.row();
        Button previous = a.button(a.t("Previous"), false, () -> {
            saveTable(false);
            tablePage--;
            a.render();
        });
        previous.setEnabled(tablePage > 0);
        Button next = a.button(a.t("Next"), false, () -> {
            saveTable(false);
            tablePage++;
            a.render();
        });
        next.setEnabled((tablePage + 1) * 20 < rows.length());
        paging.addView(previous, new LinearLayout.LayoutParams(0, a.dp(52), 1));
        paging.addView(next, new LinearLayout.LayoutParams(0, a.dp(52), 1));
        a.content.addView(paging);
        a.addButton(a.t("Save table"), true, () -> saveTable(true));
        a.addButton(a.t("Duplicate table"), false,
                () -> ui.rename("Duplicate table", table.optString("name") + " (2)", name -> {
                    JSONObject copied = StudioData.copy(table);
                    copied.remove("uuid");
                    CardStore.put(copied, "id", CardStore.uuid());
                    CardStore.put(copied, "name", name);
                    StudioData.save(a.store, "table", copied);
                    table = copied;
                    tablePage = columnPage = 0;
                    a.render();
                }));
        a.addButton(a.t("Delete table"), false,
                ()
                        -> ui.confirm("Delete table",
                                a.t("This table will be deleted. Games using it will need a new source."),
                                "Delete", () -> {
                                    a.handler.removeCallbacks(tableSave);
                                    a.store.delete(table.optString("id"));
                                    table = null;
                                    a.navigate(9);
                                }));
    }
    static TextWatcher watch(Runnable changed) {
        return new TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                changed.run();
            }
            public void afterTextChanged(Editable e) {}
        };
    }
    static boolean muted(JSONObject row, String id) {
        JSONArray muted = row.optJSONArray("muted");
        for (int i = 0; i < muted.length(); i++)
            if (id.equals(muted.optString(i)))
                return true;
        return false;
    }
    static void toggleMuted(JSONObject row, String id) {
        JSONArray old = row.optJSONArray("muted"), next = new JSONArray();
        boolean present = muted(row, id);
        for (int i = 0; i < old.length(); i++)
            if (!id.equals(old.optString(i)))
                next.put(old.optString(i));
        if (!present)
            next.put(id);
        CardStore.put(row, "muted", next);
    }
    void readTable(int row) {
        saveTable(false);
        List<TableSpeechPlan.Utterance> words = StudioData.speech(table, row);
        if (words.isEmpty()) {
            a.toast("No audible cells. Set a column reading order and unmute cells.");
            return;
        }
        a.speech.sequence(words, (float) table.optDouble("speed", 1), table.optInt("pause_ms", 500),
                a::toast, () -> a.toast("Playback complete."));
    }
    void tableSettings() {
        JSONObject next = StudioData.copy(table);
        final EditText[] name = new EditText[1], description = new EditText[1],
                         pause = new EditText[1], repeat = new EditText[1];
        final Spinner[] order = new Spinner[1], speed = new Spinner[1];
        final CheckBox[] speakers = new CheckBox[1];
        String[] speeds = {"0.5", "0.75", "1.0", "1.25", "1.5", "1.75", "2.0"};
        ui.dialog("Table settings",
                box
                -> {
                    name[0] = a.field(box, a.t("Table name"), next.optString("name"), false);
                    description[0] =
                            a.field(box, a.t("Description"), next.optString("description"), true);
                    box.addView(ui.iconPicker(
                            next.optString("icon"), value -> CardStore.put(next, "icon", value)));
                    speakers[0] = a.check(box, "Show sound buttons", next.optBoolean("speakers"));
                    order[0] = ui.options(box, "Reading order",
                            new String[] {"By row", "By column"}, new String[] {"rows", "columns"},
                            next.optString("reading_order"));
                    speed[0] = ui.options(box, "Speech speed", speeds, speeds,
                            Double.toString(next.optDouble("speed", 1)));
                    pause[0] = ui.number(box, "Pause between cells (ms)", next.optInt("pause_ms"));
                    repeat[0] = ui.number(box, "Repeat", next.optInt("repeat"));
                },
                "Save",
                () -> {
                    try {
                        CardStore.put(next, "name", name[0].getText().toString().trim());
                        CardStore.put(
                                next, "description", description[0].getText().toString().trim());
                        CardStore.put(next, "speakers", speakers[0].isChecked());
                        CardStore.put(next, "reading_order",
                                order[0].getSelectedItemPosition() == 0 ? "rows" : "columns");
                        CardStore.put(next, "speed",
                                Double.parseDouble(speeds[speed[0].getSelectedItemPosition()]));
                        CardStore.put(next, "pause_ms", ui.number(pause[0], 0, 5000));
                        CardStore.put(next, "repeat", ui.number(repeat[0], 1, 10));
                        StudioData.validateTable(next);
                        table = next;
                        saveTable(false);
                        a.render();
                        return true;
                    } catch (IllegalArgumentException invalid) {
                        a.toast(invalid.getMessage());
                        return false;
                    }
                });
    }
    void columnSettings(int index) {
        JSONObject column = table.optJSONArray("columns").optJSONObject(index);
        final EditText[] name = new EditText[1], order = new EditText[1];
        final Spinner[] language = new Spinner[1];
        final Dialog[] popup = new Dialog[1];
        popup[0] = ui.dialog("Column settings",
                box
                -> {
                    name[0] = a.field(box, a.t("Column name"), column.optString("name"), false);
                    box.addView(a.text(
                            a.t("Reading order: 0 keeps this column silent. Lower numbers play first."),
                            14, a.MUTED));
                    order[0] = ui.number(
                            box, "Speech order (0 = silent)", column.optInt("speech_order"));
                    language[0] =
                            a.languagePicker(box, "Word language", column.optString("language"));
                    box.addView(a.button(a.t("Move left"), false, () -> {
                        popup[0].dismiss();
                        move(table.optJSONArray("columns"), index, index - 1);
                        saveTable(false);
                        a.render();
                    }));
                    box.addView(a.button(a.t("Move right"), false, () -> {
                        popup[0].dismiss();
                        move(table.optJSONArray("columns"), index, index + 1);
                        saveTable(false);
                        a.render();
                    }));
                    box.addView(a.button(a.t("Delete column"), false, () -> {
                        if (table.optJSONArray("columns").length() == 1) {
                            a.toast("Keep at least one column.");
                            return;
                        }
                        ui.confirm("Delete column",
                                a.t("This column and its cells will be deleted."), "Delete", () -> {
                                    popup[0].dismiss();
                                    String id = column.optString("id");
                                    table.optJSONArray("columns").remove(index);
                                    JSONArray rows = table.optJSONArray("rows");
                                    for (int i = 0; i < rows.length(); i++) {
                                        JSONObject row = rows.optJSONObject(i);
                                        row.optJSONObject("cells").remove(id);
                                        if (muted(row, id))
                                            toggleMuted(row, id);
                                    }
                                    saveTable(false);
                                    a.render();
                                });
                    }));
                },
                "Save",
                () -> {
                    try {
                        String value = name[0].getText().toString().trim();
                        if (value.isEmpty()) {
                            name[0].setError(a.t("Please enter a name."));
                            return false;
                        }
                        CardStore.put(column, "name", value);
                        CardStore.put(column, "speech_order", ui.number(order[0], 0, 64));
                        CardStore.put(column, "language", a.languageCode(language[0]));
                        saveTable(false);
                        a.render();
                        return true;
                    } catch (IllegalArgumentException invalid) {
                        a.toast(invalid.getMessage());
                        return false;
                    }
                });
    }
    void rowSettings(int index) {
        JSONObject row = table.optJSONArray("rows").optJSONObject(index);
        final EditText[] name = new EditText[1];
        final Dialog[] popup = new Dialog[1];
        popup[0] = ui.dialog("Row settings",
                box
                -> {
                    name[0] = a.field(box, a.t("Row name"), row.optString("name"), false);
                    box.addView(a.button(a.t("Move up"), false, () -> {
                        popup[0].dismiss();
                        move(table.optJSONArray("rows"), index, index - 1);
                        saveTable(false);
                        a.render();
                    }));
                    box.addView(a.button(a.t("Move down"), false, () -> {
                        popup[0].dismiss();
                        move(table.optJSONArray("rows"), index, index + 1);
                        saveTable(false);
                        a.render();
                    }));
                    box.addView(a.button(a.t("Delete row"), false,
                            ()
                                    -> ui.confirm("Delete row",
                                            a.t("This row and its cells will be deleted."),
                                            "Delete", () -> {
                                                popup[0].dismiss();
                                                table.optJSONArray("rows").remove(index);
                                                saveTable(false);
                                                a.render();
                                            })));
                },
                "Save",
                () -> {
                    CardStore.put(row, "name", name[0].getText().toString());
                    saveTable(false);
                    a.render();
                    return true;
                });
    }
    static void move(JSONArray rows, int from, int to) {
        if (to < 0 || to >= rows.length())
            return;
        JSONObject other = rows.optJSONObject(to);
        try {
            rows.put(to, rows.get(from));
            rows.put(from, other);
        } catch (org.json.JSONException impossible) {
            throw new IllegalStateException(impossible);
        }
    }
    void pasteCells() {
        ClipboardManager clipboard =
                (ClipboardManager) a.getSystemService(Context.CLIPBOARD_SERVICE);
        String value = clipboard.hasPrimaryClip()
                ? clipboard.getPrimaryClip().getItemAt(0).coerceToText(a).toString()
                : "";
        final EditText[] field = new EditText[1];
        ui.dialog("Paste spreadsheet cells",
                box
                -> {
                    box.addView(
                            a.text(a.t("Paste tab-separated cells. Each line becomes a new row."),
                                    14, a.MUTED));
                    field[0] = a.field(box, a.t("Cells"), value, true);
                    field[0].setMinLines(6);
                },
                "Add rows",
                () -> {
                    String raw = field[0].getText().toString();
                    String[] lines = raw.split("\\r?\\n");
                    JSONArray rows = table.optJSONArray("rows"),
                              columns = table.optJSONArray("columns");
                    if (raw.trim().isEmpty() || rows.length() + lines.length > 10000) {
                        a.toast("Invalid table size");
                        return false;
                    }
                    for (String line : lines) {
                        JSONObject row = StudioData.row(Integer.toString(rows.length() + 1));
                        String[] cells = line.split("\\t", -1);
                        for (int i = 0; i < Math.min(columns.length(), cells.length); i++)
                            CardStore.put(row.optJSONObject("cells"),
                                    columns.optJSONObject(i).optString("id"), cells[i]);
                        rows.put(row);
                    }
                    saveTable(false);
                    a.render();
                    return true;
                });
    }
    void newGame(JSONObject saved) {
        capture();
        Runnable begin = () -> {
            gameDraft = saved == null ? StudioData.game() : StudioData.copy(saved);
            captureAction = null;
            a.navigate(11);
        };
        if (gameDraft != null && !gameDraft.optString("name").isEmpty()
                && (saved == null || !saved.optString("id").equals(gameDraft.optString("id"))))
            ui.confirm("Replace game draft?",
                    a.t("Your current draft will be replaced. Publish it first to keep it."),
                    "Continue", begin);
        else
            begin.run();
    }
    void designer() {
        if (gameDraft == null)
            gameDraft = StudioData.game();
        JSONObject draft = gameDraft;
        a.title(a.t("Game studio"));
        a.hint(a.t("Design, preview and publish a game in your own style."));
        a.addButton(a.t("Back to studio"), false, () -> a.navigate(9));
        EditText name = a.field(a.content, a.t("Game name"), draft.optString("name"), false),
                 description = a.field(
                         a.content, a.t("Description"), draft.optString("description"), true);
        a.content.addView(ui.iconPicker(
                draft.optString("icon"), value -> CardStore.put(draft, "icon", value)));
        Spinner mode = ui.options(a.content, "Game type", StudioData.MODE_NAMES, GameEngine.MODES,
                draft.optString("mode"));
        String[] sourceValues = {"manual", "library", "table"};
        Spinner source = ui.options(a.content, "Question source",
                new String[] {"My question pairs", "Library / deck", "My table"}, sourceValues,
                draft.optString("source"));
        boolean dictation = draft.optString("mode").equals("audio_dictation");
        EditText pairs;
        Spinner sourceId, promptCol, answerCol;
        List<String> sourceIds = new ArrayList<>(), columnIds = new ArrayList<>();
        if (draft.optString("source").equals("manual")) {
            StringBuilder lines = new StringBuilder();
            JSONArray rows = draft.optJSONArray("manual_pairs");
            for (int i = 0; i < rows.length(); i++) {
                JSONObject pair = rows.optJSONObject(i);
                if (i > 0)
                    lines.append('\n');
                lines.append(pair.optString("prompt"))
                        .append('\t')
                        .append(pair.optString("answer"));
            }
            a.hint(a.t(dictation ? "One spoken word or sentence per line. Meanings are optional."
                                 : "One question and answer per line, separated by a tab or |."));
            pairs = a.field(a.content, a.t("Question pairs"), lines.toString(), true);
            pairs.setMinLines(5);
            sourceId = promptCol = answerCol = null;
        } else {
            pairs = null;
            List<String> names = new ArrayList<>();
            boolean library = draft.optString("source").equals("library");
            if (library) {
                names.add(a.t("All decks"));
                sourceIds.add("");
            }
            for (JSONObject document : a.store.list(library ? "deck" : "table")) {
                names.add(document.optString("name"));
                sourceIds.add(document.optString(library ? "uuid" : "id"));
            }
            if (names.isEmpty()) {
                names.add(a.t("No tables yet"));
                sourceIds.add("");
            }
            a.content.addView(a.text(a.t(library ? "Deck" : "Table"), 13, a.MUTED));
            sourceId = a.spinner(
                    names, names.get(Math.max(0, sourceIds.indexOf(draft.optString("source_id")))));
            a.content.addView(sourceId);
            List<String> columnNames = new ArrayList<>();
            if (library) {
                columnIds.addAll(Arrays.asList("term", "definition"));
                columnNames.addAll(Arrays.asList(a.t("Word"), a.t("Meaning")));
            } else {
                JSONObject table = a.store.get(sourceIds.get(sourceId.getSelectedItemPosition()));
                if (table != null) {
                    JSONArray columns = table.optJSONArray("columns");
                    for (int i = 0; i < columns.length(); i++) {
                        JSONObject col = columns.optJSONObject(i);
                        columnNames.add(col.optString("name"));
                        columnIds.add(col.optString("id"));
                    }
                }
            }
            if (columnNames.isEmpty()) {
                columnNames.add(a.t("Choose a table first"));
                columnIds.add("");
            }
            a.content.addView(a.text(a.t("Question column"), 13, a.MUTED));
            promptCol = a.spinner(columnNames,
                    columnNames.get(
                            Math.max(0, columnIds.indexOf(draft.optString("prompt_column")))));
            a.content.addView(promptCol);
            answerCol = a.spinner(columnNames,
                    columnNames.get(
                            Math.max(0, columnIds.indexOf(draft.optString("answer_column")))));
            if (!dictation) {
                a.content.addView(a.text(a.t("Answer column"), 13, a.MUTED));
                a.content.addView(answerCol);
            }
        }
        Spinner language = a.languagePicker(
                        a.content, "Question language", draft.optString("language", "en")),
                answerLanguage = a.languagePicker(
                        a.content, "Answer language", draft.optString("answer_language", "tr"));
        if (dictation)
            answerLanguage.setVisibility(View.GONE);
        EditText count = ui.number(
                         a.content, "Questions per game", draft.optInt("question_count", 10)),
                 limit = ui.number(a.content, "Seconds per question (0 = unlimited)",
                         draft.optInt("time_limit"));
        CheckBox shuffle = a.check(a.content, "Shuffle questions", draft.optBoolean("shuffle")),
                 hints = a.check(a.content, "Allow hints", draft.optBoolean("hints")),
                 sound = a.check(a.content, "Sound effects", draft.optBoolean("sound"));
        captureAction = () -> {
            CardStore.put(draft, "name", name.getText().toString().trim());
            CardStore.put(draft, "description", description.getText().toString().trim());
            CardStore.put(draft, "mode", GameEngine.MODES[mode.getSelectedItemPosition()]);
            CardStore.put(draft, "source", sourceValues[source.getSelectedItemPosition()]);
            CardStore.put(draft, "language", a.languageCode(language));
            CardStore.put(draft, "answer_language", a.languageCode(answerLanguage));
            CardStore.put(
                    draft, "question_count", safeInt(count, draft.optInt("question_count", 10)));
            CardStore.put(draft, "time_limit", safeInt(limit, draft.optInt("time_limit")));
            CardStore.put(draft, "shuffle", shuffle.isChecked());
            CardStore.put(draft, "hints", hints.isChecked());
            CardStore.put(draft, "sound", sound.isChecked());
            if (pairs != null) {
                JSONArray rows = new JSONArray();
                for (String line : pairs.getText().toString().split("\\r?\\n")) {
                    if (line.trim().isEmpty())
                        continue;
                    String[] cells = line.split("\\t|\\|", 2);
                    JSONObject row = new JSONObject();
                    CardStore.put(row, "prompt", cells[0].trim());
                    CardStore.put(row, "answer", cells.length == 2 ? cells[1].trim() : "");
                    rows.put(row);
                }
                CardStore.put(draft, "manual_pairs", rows);
            } else {
                CardStore.put(
                        draft, "source_id", sourceIds.get(sourceId.getSelectedItemPosition()));
                CardStore.put(
                        draft, "prompt_column", columnIds.get(promptCol.getSelectedItemPosition()));
                CardStore.put(
                        draft, "answer_column", columnIds.get(answerCol.getSelectedItemPosition()));
            }
        };
        a.selection(mode, pos -> {
            capture();
            captureAction = null;
            if (GameEngine.board(draft.optString("mode")))
                CardStore.put(draft, "question_count", Math.min(8, draft.optInt("question_count")));
            a.render();
        });
        a.selection(source, pos -> {
            capture();
            captureAction = null;
            CardStore.put(draft, "source_id", "");
            CardStore.put(draft, "prompt_column", "term");
            CardStore.put(draft, "answer_column", "definition");
            a.render();
        });
        if (sourceId != null)
            a.selection(sourceId, pos -> {
                capture();
                captureAction = null;
                CardStore.put(draft, "prompt_column", "");
                CardStore.put(draft, "answer_column", "");
                a.render();
            });
        a.addButton(a.t("Play preview"), false, () -> {
            capture();
            if (draft.optString("name").isEmpty())
                CardStore.put(draft, "name", a.t("Game preview"));
            try {
                ui.number(count, 1, GameEngine.board(draft.optString("mode")) ? 8 : 100);
                ui.number(limit, 0, 300);
                startGame(draft, true);
            } catch (IllegalArgumentException invalid) {
                a.toast(invalid.getMessage());
            }
        });
        a.addButton(a.t("Publish to extensions"), true, () -> {
            try {
                capture();
                ui.number(count, 1, GameEngine.board(draft.optString("mode")) ? 8 : 100);
                ui.number(limit, 0, 300);
                StudioData.questions(a.store, draft);
                StudioData.save(a.store, "game", draft);
                a.toast("Game saved. Add it to your menu from Extensions.");
            } catch (IllegalArgumentException invalid) {
                a.toast(invalid.getMessage());
            }
        });
        if (a.store.get(draft.optString("id")) != null)
            a.addButton(a.t("Delete game"), false,
                    ()
                            -> ui.confirm("Delete game",
                                    a.t("The game and its saved scores will be deleted."), "Delete",
                                    () -> {
                                        a.store.delete(draft.optString("id"));
                                        captureAction = null;
                                        gameDraft = null;
                                        a.navigate(9);
                                    }));
    }
    static int safeInt(EditText field, int fallback) {
        try {
            return Integer.parseInt(field.getText().toString());
        } catch (NumberFormatException invalid) {
            return fallback;
        }
    }
    void startGame(JSONObject game, boolean preview) {
        try {
            List<GameEngine.Pair> pool = StudioData.questions(a.store, game);
            pause();
            session = new GameEngine(game.optString("mode"), pool, game.optInt("question_count"),
                    game.optBoolean("shuffle"), new Random());
            playing = StudioData.copy(game);
            this.preview = preview;
            recorded = false;
            elapsed = 0;
            remaining = game.optInt("time_limit") * 1000;
            feedbackText = "";
            a.navigate(12);
        } catch (IllegalArgumentException invalid) {
            a.toast(invalid.getMessage());
        }
    }
    void player() {
        captureAction = null;
        if (session == null) {
            home();
            return;
        }
        a.title(playing.optString("name"));
        a.hint(a.t(preview ? "Preview · scores are not saved"
                        : a.store.get(playing.optString("id")) != null ? "Published game"
                                                                       : "Practice Quiz"));
        a.addButton(
                a.t(preview ? "Back to designer"
                                : a.store.get(playing.optString("id")) != null ? "Back to studio"
                                                                               : "Back to library"),
                false, () -> {
                    pause();
                    a.navigate(preview ? 11 : a.store.get(playing.optString("id")) != null ? 9 : 2);
                });
        if (session.complete()) {
            pause();
            if (!preview && !recorded && a.store.get(playing.optString("id")) != null) {
                a.store.recordGame(
                        playing.optString("id"), session.correct, session.items.size(), elapsed);
                recorded = true;
            }
            a.content.addView(a.text(a.t("Session complete!"), 24, a.GREEN));
            a.hint(a.t("Score: {correct}/{total} · Mistakes: {mistakes}", "correct",
                    session.correct, "total", session.items.size(), "mistakes", session.mistakes));
            a.addButton(a.t("Play again"), true, () -> startGame(playing, preview));
            return;
        }
        a.hint(a.t("Score: {correct}/{total} · Mistakes: {mistakes}", "correct", session.correct,
                "total", session.items.size(), "mistakes", session.mistakes));
        clock = a.text("", 14, a.MUTED);
        a.content.addView(clock);
        feedback = a.text(feedbackText, 16, a.GREEN);
        a.content.addView(feedback);
        if (GameEngine.board(session.mode)) {
            board();
        } else {
            GameEngine.Pair pair = session.current();
            boolean audio = GameEngine.audio(session.mode);
            LinearLayout question = a.panel();
            question.addView(a.text(audio                         ? a.t("Listen carefully")
                            : session.mode.equals("word_builder") ? pair.answer
                                                                  : pair.prompt,
                    25, a.INK));
            a.content.addView(question);
            a.hint((session.index + 1) + " / " + session.items.size());
            a.addButton(a.t("Listen"), false, this::listenQuestion);
            if (session.locked) {
                feedback.setText(feedbackText);
                a.addButton(a.t("Next Question"), true, this::nextQuestion);
            } else if (GameEngine.choice(session.mode)) {
                for (String option : session.choices())
                    a.addButton(option, false, () -> submit(option));
            } else if (session.mode.equals("word_builder")) {
                letters();
            } else {
                EditText answer = a.field(a.content, a.t("Your answer"), "", false);
                answer.setInputType(android.text.InputType.TYPE_CLASS_TEXT);
                a.addButton(a.t("Check"), true, () -> {
                    if (!answer.getText().toString().trim().isEmpty())
                        submit(answer.getText().toString());
                });
                answer.setOnEditorActionListener((view, id, event) -> {
                    submit(answer.getText().toString());
                    return true;
                });
            }
            if (!session.locked) {
                if (playing.optBoolean("hints"))
                    a.addButton(a.t("Hint"), false, () -> {
                        String expected = session.expected();
                        int end = expected.offsetByCodePoints(0, 1);
                        feedback.setText(expected.substring(0, end) + "…");
                    });
                a.addButton(a.t("Skip question"), false, () -> submit(""));
            }
            audioReady = !audio;
            if (audio && a.resumed && !session.locked && a.store.flag("practice_autoplay", true))
                a.handler.post(this::listenQuestion);
            if (a.store.flag("audio_prefetch", true) && session.index + 1 < session.items.size()) {
                GameEngine.Pair upcoming = session.items.get(session.index + 1);
                a.handler.postDelayed(() -> {
                    if (a.page == 12 && session != null && !session.complete())
                        a.speech.prefetch(upcoming.prompt, upcoming.language);
                }, 500);
            }
        }
        active = a.resumed;
        startTime = lastTick = android.os.SystemClock.elapsedRealtime();
        a.handler.removeCallbacks(ticker);
        if (active)
            a.handler.post(ticker);
    }
    void listenQuestion() {
        if (a.page != 12 || session == null || session.complete() || GameEngine.board(session.mode)
                || session.locked || !a.resumed)
            return;
        int ticket = ++playerGeneration;
        audioReady = false;
        lastTick = android.os.SystemClock.elapsedRealtime();
        GameEngine.Pair pair = session.current();
        if (feedback != null)
            feedback.setText(a.t("Preparing audio…"));
        a.speech.play(pair.prompt, pair.language, a.store.decimal("speech_speed", 1),
                a.store.number("speech_volume", 100) / 100f,
                error
                -> {
                    if (ticket == playerGeneration && a.page == 12) {
                        audioReady = false;
                        if (feedback != null)
                            feedback.setText(a.t(error));
                    }
                },
                () -> {
                    if (ticket == playerGeneration && a.page == 12) {
                        audioReady = true;
                        lastTick = android.os.SystemClock.elapsedRealtime();
                        if (feedback != null)
                            feedback.setText("");
                    }
                });
    }
    void submit(String answer) {
        if (session == null || session.complete() || session.locked)
            return;
        Boolean right = session.answer(answer);
        if (right == null)
            return;
        playerGeneration++;
        a.speech.stop();
        feedbackText = a.t(right ? "Correct!" : "Wrong! Correct answer: {answer}", "answer",
                session.expected());
        if (!preview && !session.current().cardId.isEmpty())
            a.store.recordPractice(session.current().cardId,
                    playing.optString("practice_mode", session.mode), answer, session.expected(),
                    right);
        if (playing.optBoolean("sound"))
            a.extras.sound(right);
        pause();
        a.render();
        if (right && a.store.flag("practice_auto_next", true)) {
            int index = session.index, ticket = playerGeneration;
            a.handler.postDelayed(() -> {
                if (a.page == 12 && session != null && session.locked && session.index == index
                        && ticket == playerGeneration)
                    nextQuestion();
            }, a.store.number("practice_advance_ms", 300));
        }
    }
    void nextQuestion() {
        pause();
        session.advance();
        remaining = playing.optInt("time_limit") * 1000;
        feedbackText = "";
        a.render();
    }
    void tick() {
        if (!active || session == null || session.complete())
            return;
        long now = android.os.SystemClock.elapsedRealtime(), delta = now - lastTick;
        lastTick = now;
        if (playing.optInt("time_limit") > 0 && !session.locked
                && (audioReady || !GameEngine.audio(session.mode))) {
            remaining -= Math.max(0, delta);
            clock.setText(
                    a.t("Time left: {seconds}s", "seconds", Math.max(0, (remaining + 999) / 1000)));
            if (remaining <= 0) {
                if (GameEngine.board(session.mode)) {
                    for (int i = 0; i < session.items.size(); i++)
                        if (!session.matched.contains(i))
                            session.mistakes++;
                    session.matched.addAll(allIndices());
                    pause();
                    a.render();
                } else
                    submit("");
            }
        }
    }
    Set<Integer> allIndices() {
        Set<Integer> ids = new HashSet<>();
        for (int i = 0; i < session.items.size(); i++) ids.add(i);
        return ids;
    }
    void board() {
        boolean memory = session.mode.equals("memory");
        int count = session.items.size();
        List<Integer> order = new ArrayList<>();
        for (int i = 0; i < count * 2; i++) order.add(i);
        Collections.shuffle(order, session.random);
        final int[] selected = {-1};
        final boolean[] locked = {false};
        final Button[] cards = new Button[count * 2];
        int ticket = ++playerGeneration;
        for (int start = 0; start < order.size(); start += 2) {
            LinearLayout row = a.row();
            for (int pos = start; pos < Math.min(start + 2, order.size()); pos++) {
                int tile = order.get(pos), pairIndex = tile % count;
                boolean answer = tile >= count;
                GameEngine.Pair pair = session.items.get(pairIndex);
                String label = answer ? pair.answer : pair.prompt;
                Button card = a.button(memory ? a.t("Tap to reveal") : label, false, () -> {});
                cards[tile] = card;
                card.setMinHeight(a.dp(88));
                card.setEnabled(!session.matched.contains(pairIndex));
                if (session.matched.contains(pairIndex))
                    card.setText("✓ " + label);
                card.setOnClickListener(view -> {
                    if (locked[0] || session.matched.contains(pairIndex) || selected[0] == tile)
                        return;
                    card.setText(label);
                    if (selected[0] < 0) {
                        selected[0] = tile;
                        card.setBackground(a.background(Color.rgb(25, 65, 58), 12));
                        return;
                    }
                    int first = selected[0];
                    boolean opposite = (first < count) != (tile < count);
                    Boolean right = opposite ? session.match(first % count, pairIndex) : false;
                    if (!opposite)
                        session.mistakes++;
                    selected[0] = -1;
                    if (Boolean.TRUE.equals(right)) {
                        cards[first].setEnabled(false);
                        card.setEnabled(false);
                        feedback.setText(a.t("Correct!"));
                        if (playing.optBoolean("sound"))
                            a.extras.sound(true);
                        if (session.complete()) {
                            pause();
                            a.render();
                        }
                    } else {
                        locked[0] = true;
                        feedback.setText(a.t("Try again"));
                        if (playing.optBoolean("sound"))
                            a.extras.sound(false);
                        a.handler.postDelayed(() -> {
                            if (ticket != playerGeneration || a.page != 12)
                                return;
                            if (memory) {
                                cards[first].setText(a.t("Tap to reveal"));
                                card.setText(a.t("Tap to reveal"));
                            }
                            cards[first].setBackground(a.background(Color.rgb(29, 39, 57), 12));
                            locked[0] = false;
                        }, 700);
                    }
                });
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, -2, 1);
                lp.setMargins(a.dp(4), a.dp(4), a.dp(4), a.dp(4));
                row.addView(card, lp);
            }
            a.content.addView(row);
        }
    }
    void letters() {
        List<String> characters = new ArrayList<>();
        session.current().prompt.codePoints().forEach(
                code -> characters.add(new String(Character.toChars(code))));
        Collections.shuffle(characters, session.random);
        List<Integer> used = new ArrayList<>();
        TextView assembled = a.text("", 25, a.GREEN);
        a.content.addView(assembled);
        List<Button> tiles = new ArrayList<>();
        Button check = a.button(a.t("Check"), true, () -> submit(assembled.getText().toString()));
        check.setEnabled(false);
        Runnable update = () -> {
            StringBuilder value = new StringBuilder();
            for (int index : used) value.append(characters.get(index));
            assembled.setText(value);
            check.setEnabled(used.size() == characters.size());
        };
        for (int start = 0; start < characters.size(); start += 5) {
            LinearLayout row = a.row();
            for (int i = start; i < Math.min(start + 5, characters.size()); i++) {
                int index = i;
                Button tile = a.button(
                        characters.get(i).equals(" ") ? "␣" : characters.get(i), false, () -> {});
                tile.setOnClickListener(v -> {
                    if (session.locked)
                        return;
                    used.add(index);
                    tile.setEnabled(false);
                    update.run();
                });
                tiles.add(tile);
                row.addView(tile, new LinearLayout.LayoutParams(0, a.dp(56), 1));
            }
            a.content.addView(row);
        }
        a.addButton(a.t("Undo"), false, () -> {
            if (!used.isEmpty()) {
                tiles.get(used.remove(used.size() - 1)).setEnabled(true);
                update.run();
            }
        });
        a.addButton(a.t("Clear"), false, () -> {
            used.clear();
            for (Button tile : tiles) tile.setEnabled(true);
            update.run();
        });
        a.content.addView(check);
    }
    JSONObject state() {
        capture();
        saveTable(false);
        JSONObject value = new JSONObject();
        CardStore.put(value, "table_id", table == null ? "" : table.optString("id"));
        CardStore.put(value, "table_page", tablePage);
        CardStore.put(value, "column_page", columnPage);
        if (gameDraft != null)
            CardStore.put(value, "draft", gameDraft);
        if (session != null && playing != null) {
            CardStore.put(value, "playing", playing);
            CardStore.put(value, "preview", preview);
            CardStore.put(value, "recorded", recorded);
            CardStore.put(value, "elapsed",
                    elapsed
                            + (active ? Math.max(0,
                                                android.os.SystemClock.elapsedRealtime()
                                                        - startTime)
                                      : 0));
            CardStore.put(value, "remaining", remaining);
            CardStore.put(value, "feedback", feedbackText);
            CardStore.put(value, "index", session.index);
            CardStore.put(value, "correct", session.correct);
            CardStore.put(value, "mistakes", session.mistakes);
            CardStore.put(value, "locked", session.locked);
            CardStore.put(value, "matched", new JSONArray(session.matched));
            JSONArray items = new JSONArray();
            for (GameEngine.Pair pair : session.items) {
                JSONObject p = new JSONObject();
                CardStore.put(p, "prompt", pair.prompt);
                CardStore.put(p, "answer", pair.answer);
                CardStore.put(p, "language", pair.language);
                CardStore.put(p, "answer_language", pair.answerLanguage);
                CardStore.put(p, "card_id", pair.cardId);
                items.put(p);
            }
            CardStore.put(value, "items", items);
        }
        return value;
    }
    void restore(JSONObject state) {
        table = a.store.get(state.optString("table_id"));
        tablePage = state.optInt("table_page");
        columnPage = state.optInt("column_page");
        gameDraft = state.optJSONObject("draft");
        playing = state.optJSONObject("playing");
        if (playing != null) {
            try {
                List<GameEngine.Pair> pairs = new ArrayList<>();
                JSONArray saved = state.optJSONArray("items");
                for (int i = 0; i < saved.length(); i++) {
                    JSONObject p = saved.optJSONObject(i);
                    pairs.add(new GameEngine.Pair(p.optString("prompt"), p.optString("answer"),
                            p.optString("language"), p.optString("answer_language"),
                            p.optString("card_id")));
                }
                session = new GameEngine(
                        playing.optString("mode"), pairs, pairs.size(), false, new Random());
                session.index = state.optInt("index");
                session.correct = state.optInt("correct");
                session.mistakes = state.optInt("mistakes");
                session.locked = state.optBoolean("locked");
                JSONArray matched = state.optJSONArray("matched");
                for (int i = 0; i < matched.length(); i++) session.matched.add(matched.optInt(i));
                preview = state.optBoolean("preview");
                recorded = state.optBoolean("recorded");
                elapsed = state.optLong("elapsed");
                remaining = state.optInt("remaining");
                feedbackText = state.optString("feedback");
            } catch (Exception invalid) {
                session = null;
                playing = null;
            }
        }
    }
    void reset() {
        a.handler.removeCallbacks(tableSave);
        pause();
        captureAction = null;
        table = gameDraft = playing = null;
        session = null;
        tablePage = columnPage = 0;
    }
}
