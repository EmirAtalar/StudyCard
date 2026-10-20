package com.studycard.app;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;
import java.util.ArrayList;
import java.util.List;
import org.json.JSONObject;

/** A real Android home-screen counterpart of the desktop vocabulary widget. */
public final class StudyWidget extends AppWidgetProvider {
    private static final String NEXT = "com.studycard.app.WIDGET_NEXT";
    static void refresh(Context context) {
        AppWidgetManager manager = AppWidgetManager.getInstance(context);
        int[] ids = manager.getAppWidgetIds(new ComponentName(context, StudyWidget.class));
        if (ids.length > 0)
            new StudyWidget().onUpdate(context, manager, ids);
    }
    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] ids) {
        try (CardStore store = new CardStore(context)) {
            L10n language = new L10n(context, store.config("ui_language", "tr"));
            List<JSONObject> cards = store.list("card");
            List<JSONObject> due = new ArrayList<>();
            String today = java.time.LocalDate.now().toString();
            for (JSONObject card : cards)
                if (card.optString("status").equals("new")
                        || card.optString("due_date", today).compareTo(today) <= 0)
                    due.add(card);
            if (!due.isEmpty())
                cards = due;
            JSONObject card = cards.isEmpty()
                    ? null
                    : cards.get(Math.floorMod(store.number("widget_index", 0), cards.size()));
            for (int id : ids) {
                RemoteViews views =
                        new RemoteViews(context.getPackageName(), R.layout.study_widget);
                views.setTextViewText(R.id.widget_term,
                        card == null ? language.get("Add your first word")
                                     : card.optString("term"));
                views.setTextViewText(R.id.widget_meaning,
                        card == null ? language.get("A few words every day")
                                     : card.optString("definition"));
                views.setTextViewText(R.id.widget_open, language.get("Study"));
                views.setTextViewText(R.id.widget_next, language.get("Next"));
                Intent open = new Intent(context, MainActivity.class).putExtra("route", "study");
                if (card != null)
                    open.putExtra("widget_card", card.optString("uuid"));
                views.setOnClickPendingIntent(R.id.widget_open,
                        PendingIntent.getActivity(context, id, open,
                                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));
                views.setOnClickPendingIntent(R.id.widget_next,
                        PendingIntent.getBroadcast(context, id,
                                new Intent(context, StudyWidget.class).setAction(NEXT),
                                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE));
                manager.updateAppWidget(id, views);
            }
        }
    }
    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        if (NEXT.equals(intent.getAction())) {
            try (CardStore store = new CardStore(context)) {
                store.configSet(
                        "widget_index", Integer.toString(store.number("widget_index", 0) + 1));
            }
            refresh(context);
        }
    }
}
