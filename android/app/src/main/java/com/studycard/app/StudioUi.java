package com.studycard.app;

import android.app.Dialog;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import java.util.Arrays;
import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

/** All creator popups use the app's colors, spacing and buttons. */
final class StudioUi {
    final MainActivity a;
    StudioUi(MainActivity activity) {
        a = activity;
    }
    Dialog dialog(
            String title, Consumer<LinearLayout> build, String action, BooleanSupplier accept) {
        Dialog dialog = new Dialog(a);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout shell = a.column();
        shell.setPadding(a.dp(20), a.dp(14), a.dp(20), a.dp(18));
        shell.setBackground(a.background(a.PANEL, 20));
        shell.addView(a.text(a.t(title), 23, a.INK));
        ScrollView scroll = new ScrollView(a);
        LinearLayout fields = a.column();
        scroll.addView(fields);
        shell.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        build.accept(fields);
        LinearLayout actions = a.row();
        Button cancel = a.button(a.t("Cancel"), false, dialog::dismiss);
        actions.addView(cancel, new LinearLayout.LayoutParams(0, a.dp(52), 1));
        if (accept != null) {
            Button save = a.button(a.t(action), true, () -> {
                if (accept.getAsBoolean())
                    dialog.dismiss();
            });
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, a.dp(52), 1);
            lp.setMargins(a.dp(8), 0, 0, 0);
            actions.addView(save, lp);
        }
        shell.addView(actions);
        dialog.setContentView(shell);
        dialog.show();
        Window window = dialog.getWindow();
        if (window != null) {
            window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            int height = (int) (a.getResources().getDisplayMetrics().heightPixels * .84);
            window.setLayout(Math.min(a.getResources().getDisplayMetrics().widthPixels - a.dp(24),
                                     a.dp(620)),
                    height);
            window.setGravity(Gravity.CENTER);
            window.setSoftInputMode(
                    android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        }
        return dialog;
    }
    void confirm(String title, String message, String action, Runnable accepted) {
        dialog(title, box -> box.addView(a.text(message, 16, a.MUTED)), action, () -> {
            accepted.run();
            return true;
        });
    }
    void rename(String title, String current, Consumer<String> saved) {
        final EditText[] field = new EditText[1];
        dialog(title, box -> field[0] = a.field(box, a.t("Name"), current, false), "Save", () -> {
            String name = field[0].getText().toString().trim();
            if (name.isEmpty()) {
                field[0].setError(a.t("Please enter a name."));
                return false;
            }
            saved.accept(name);
            return true;
        });
    }
    Button iconPicker(String selected, Consumer<String> changed) {
        Button trigger = a.button(a.t("Choose an icon"), false, () -> {});
        final String[] active = {selected};
        a.icon(trigger, selected);
        trigger.setOnClickListener(v -> {
            final Dialog[] popup = new Dialog[1];
            popup[0] = dialog("Choose an icon", box -> {
                for (int start = 0; start < StudioData.ICONS.length; start += 4) {
                    LinearLayout row = a.row();
                    for (int i = start; i < Math.min(start + 4, StudioData.ICONS.length); i++) {
                        String key = StudioData.ICONS[i], name = StudioData.ICON_NAMES[i];
                        Button choice = a.button(a.t(name), key.equals(active[0]), () -> {
                            active[0] = key;
                            a.icon(trigger, key);
                            changed.accept(key);
                            popup[0].dismiss();
                        });
                        a.icon(choice, key);
                        choice.setTextSize(11);
                        choice.setCompoundDrawablePadding(a.dp(3));
                        choice.setMinHeight(a.dp(64));
                        LinearLayout.LayoutParams lp =
                                new LinearLayout.LayoutParams(0, a.dp(76), 1);
                        lp.setMargins(a.dp(3), a.dp(3), a.dp(3), a.dp(3));
                        row.addView(choice, lp);
                    }
                    box.addView(row);
                }
            }, null, null);
        });
        return trigger;
    }
    Spinner options(
            LinearLayout box, String label, String[] names, String[] values, String selected) {
        box.addView(a.text(a.t(label), 13, a.MUTED));
        String[] localized = new String[names.length];
        for (int i = 0; i < names.length; i++)
            localized[i] = a.t(names[i]);
        int index = Arrays.asList(values).indexOf(selected);
        Spinner picker = a.spinner(Arrays.asList(localized), localized[Math.max(0, index)]);
        box.addView(picker);
        return picker;
    }
    EditText number(LinearLayout box, String label, int value) {
        EditText field = a.field(box, a.t(label), Integer.toString(value), false);
        field.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        return field;
    }
    int number(EditText field, int low, int high) {
        try {
            int value = Integer.parseInt(field.getText().toString());
            if (value >= low && value <= high)
                return value;
        } catch (NumberFormatException ignored) {
        }
        field.setError(a.t("Choose a value between {min} and {max}.", "min", low, "max", high));
        throw new IllegalArgumentException(a.t("Check the highlighted values."));
    }
}
