package com.studycard.app;

import android.Manifest;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import java.time.LocalTime;
import java.time.ZonedDateTime;

/** Inexact Android alarms respect the OS battery rules; no domain or Google account. */
public final class MobileReminders extends BroadcastReceiver {
    private static final String DAILY = "com.studycard.app.DAILY",
                                TIMER = "com.studycard.app.TIMER";
    private static PendingIntent alarm(Context context, String action, int code) {
        return PendingIntent.getBroadcast(context, code,
                new Intent(context, MobileReminders.class).setAction(action),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }
    static void schedule(Context context, CardStore store) {
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        PendingIntent intent = alarm(context, DAILY, 301);
        manager.cancel(intent);
        if (!store.flag("daily_notification_enabled", false))
            return;
        try {
            LocalTime time = LocalTime.parse(store.config("notification_time", "20:00"));
            ZonedDateTime next = ZonedDateTime.now()
                                         .withHour(time.getHour())
                                         .withMinute(time.getMinute())
                                         .withSecond(0)
                                         .withNano(0);
            if (!next.isAfter(ZonedDateTime.now()))
                next = next.plusDays(1);
            manager.setAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP, next.toInstant().toEpochMilli(), intent);
        } catch (java.time.DateTimeException invalid) {
            store.configSet("daily_notification_enabled", "false");
        }
    }
    static void scheduleTimer(Context context, CardStore store) {
        cancelTimer(context);
        if (!store.flag("timer_running", false)
                || store.config("timer_mode", "timer").equals("stopwatch"))
            return;
        long started;
        try {
            started = Long.parseLong(store.config("timer_started", "0"));
        } catch (NumberFormatException invalid) {
            return;
        }
        long deadline = started
                + Math.max(0,
                          store.number("timer_duration", 1500) - store.number("timer_elapsed", 0))
                        * 1000L;
        ((AlarmManager) context.getSystemService(Context.ALARM_SERVICE))
                .setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,
                        Math.max(System.currentTimeMillis() + 1000, deadline),
                        alarm(context, TIMER, 302));
    }
    static void cancelTimer(Context context) {
        ((AlarmManager) context.getSystemService(Context.ALARM_SERVICE))
                .cancel(alarm(context, TIMER, 302));
    }
    static void notify(Context context, String title, String body, int id, String route) {
        if (Build.VERSION.SDK_INT >= 33
                && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                        != PackageManager.PERMISSION_GRANTED)
            return;
        NotificationManager manager =
                (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        manager.createNotificationChannel(new NotificationChannel(
                "learning", "Studycard", NotificationManager.IMPORTANCE_DEFAULT));
        PendingIntent open = PendingIntent.getActivity(context, id,
                new Intent(context, MainActivity.class).putExtra("route", route),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification notification = new Notification.Builder(context, "learning")
                                            .setSmallIcon(R.drawable.ic_notification)
                                            .setContentTitle(title)
                                            .setContentText(body)
                                            .setStyle(new Notification.BigTextStyle().bigText(body))
                                            .setAutoCancel(true)
                                            .setContentIntent(open)
                                            .build();
        manager.notify(id, notification);
    }
    @Override
    public void onReceive(Context context, Intent intent) {
        try (CardStore store = new CardStore(context)) {
            L10n language = new L10n(context, store.config("ui_language", "tr"));
            if (TIMER.equals(intent.getAction())) {
                if (store.flag("timer_running", false)
                        && store.config("timer_mode", "timer").equals("timer")) {
                    if (store.timerElapsed() >= store.number("timer_duration", 1500)) {
                        store.finishTimer(true);
                        notify(context, language.get("Focus session complete!"),
                                language.get("Your focus time was saved to statistics."), 402,
                                "timer");
                    } else
                        scheduleTimer(context, store);
                }
            } else if (DAILY.equals(intent.getAction())) {
                if (store.flag("daily_notification_enabled", false))
                    notify(context, language.get("A few words every day"),
                            language.get("Your daily goal: {goal} words", "goal",
                                    store.config("daily_goal", "10")),
                            401, "study");
                schedule(context, store);
            } else {
                schedule(context, store);
                scheduleTimer(context, store);
            }
            StudyWidget.refresh(context);
        }
    }
}
