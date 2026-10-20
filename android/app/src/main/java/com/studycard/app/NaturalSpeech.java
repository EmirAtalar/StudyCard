package com.studycard.app;

import android.content.Context;
import android.media.MediaPlayer;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.speech.tts.Voice;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Consumer;

/** Highest-quality installed voice; pre-synthesized upcoming sentences start immediately. */
final class NaturalSpeech {
    private final TextToSpeech engine;
    private final Context context;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final Map<String, File> pending = new ConcurrentHashMap<>();
    private boolean ready, initialized;
    private volatile boolean closed;
    private Runnable waitingPlay;
    private MediaPlayer player;
    private volatile int generation = 0;
    private Consumer<String> activeError;
    private Runnable activeDone;
    private String activeId = "";
    private int serial;
    private float defaultSpeed = 1f, defaultVolume = 1f;
    NaturalSpeech(Context context) {
        this.context = context.getApplicationContext();
        engine = new TextToSpeech(this.context, status -> main.post(() -> {
            initialized = true;
            ready = status == TextToSpeech.SUCCESS;
            Runnable waiting = waitingPlay;
            waitingPlay = null;
            if (waiting != null && !closed)
                waiting.run();
        }));
        engine.setOnUtteranceProgressListener(new UtteranceProgressListener() {
            public void onStart(String id) {}
            public void onDone(String id) {
                File part = pending.remove(id);
                if (part != null && part.length() > 0)
                    part.renameTo(new File(part.getPath().replace(".part", ".wav")));
                main.post(() -> {
                    if (!closed && id.equals(activeId))
                        finish();
                });
            }
            public void onError(String id) {
                File part = pending.remove(id);
                if (part != null)
                    part.delete();
                main.post(() -> {
                    if (!closed && id.equals(activeId) && activeError != null)
                        activeError.accept("Audio could not play. Retry or choose another card.");
                });
            }
            @Override
            public void onStop(String id, boolean interrupted) {
                File part = pending.remove(id);
                if (part != null)
                    part.delete();
            }
        });
    }
    private Voice voice(String language) {
        if (!ready || engine.getVoices() == null)
            return null;
        String code = Locale.forLanguageTag(language).getLanguage();
        Voice best = null;
        android.net.ConnectivityManager connectivity =
                (android.net.ConnectivityManager) context.getSystemService(
                        Context.CONNECTIVITY_SERVICE);
        boolean connected = connectivity != null && connectivity.getActiveNetwork() != null;
        for (Voice voice : engine.getVoices()) {
            if (!code.equals(voice.getLocale().getLanguage())
                    || (voice.isNetworkConnectionRequired() && !connected))
                continue;
            if (voice.getFeatures() != null
                    && voice.getFeatures().contains(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED))
                continue;
            if (best == null || voice.getQuality() > best.getQuality()
                    || (voice.getQuality() == best.getQuality()
                            && voice.getLatency() < best.getLatency()))
                best = voice;
        }
        return best;
    }
    private File cached(String text, String language, Voice voice, float speed) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] data = digest.digest(
                    ("natural-v3:" + language + ":" + voice.getName() + ":" + speed + ":" + text)
                            .getBytes(StandardCharsets.UTF_8));
            StringBuilder key = new StringBuilder();
            for (byte value : data)
                key.append(String.format(Locale.ROOT, "%02x", value));
            File directory = new File(context.getCacheDir(), "speech");
            directory.mkdirs();
            return new File(directory, key + ".wav");
        } catch (Exception impossible) {
            throw new IllegalStateException(impossible);
        }
    }
    void configure(float speed, int volume) {
        defaultSpeed = Math.max(.5f, Math.min(2f, speed));
        defaultVolume = Math.max(0, Math.min(100, volume)) / 100f;
    }
    void play(String text, String language, Consumer<String> error) {
        play(text, language, defaultSpeed, defaultVolume, error, () -> {});
    }
    void play(String text, String language, float speed, float volume, Consumer<String> error,
            Runnable done) {
        stop();
        playSingle(text, language, speed, volume, error, done, generation);
    }
    private void finish() {
        Runnable done = activeDone;
        activeDone = null;
        activeError = null;
        activeId = "";
        if (done != null)
            done.run();
    }
    private void playSingle(String text, String language, float speed, float volume,
            Consumer<String> error, Runnable done, int request) {
        if (closed || request != generation)
            return;
        if (!initialized) {
            waitingPlay = () -> playSingle(text, language, speed, volume, error, done, request);
            return;
        }
        activeError = error;
        activeDone = done;
        activeId = "play-" + request + "-" + (++serial);
        if (text.trim().isEmpty()) {
            finish();
            return;
        }
        if (!ready) {
            error.accept("Install the Android voice pack for this language.");
            return;
        }
        Voice selected = voice(language);
        if (selected == null || selected.getQuality() < Voice.QUALITY_NORMAL) {
            error.accept("Install the Android voice pack for this language.");
            return;
        }
        float rate = Math.max(.5f, Math.min(2f, speed));
        File file = cached(text, language, selected, rate);
        if (file.length() > 0) {
            try {
                player = new MediaPlayer();
                MediaPlayer current = player;
                current.setDataSource(file.getPath());
                current.setVolume(volume, volume);
                current.setOnPreparedListener(prepared -> {
                    if (!closed && generation == request)
                        prepared.start();
                });
                current.setOnCompletionListener(completed -> {
                    completed.release();
                    if (player == completed)
                        player = null;
                    if (!closed && generation == request)
                        finish();
                });
                current.setOnErrorListener((failed, what, extra) -> {
                    failed.release();
                    if (player == failed)
                        player = null;
                    file.delete();
                    if (generation == request)
                        error.accept("Audio could not play. Retry or choose another card.");
                    return true;
                });
                current.prepareAsync();
                return;
            } catch (Exception failure) {
                if (player != null) {
                    player.release();
                    player = null;
                }
                file.delete();
            }
        }
        if (engine.setVoice(selected) != TextToSpeech.SUCCESS) {
            error.accept("Install the Android voice pack for this language.");
            return;
        }
        engine.setSpeechRate(rate);
        engine.setPitch(1f);
        android.os.Bundle options = new android.os.Bundle();
        options.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME, volume);
        if (engine.speak(text, TextToSpeech.QUEUE_FLUSH, options, activeId) != TextToSpeech.SUCCESS)
            error.accept("Install the Android voice pack for this language.");
    }
    void sequence(java.util.List<TableSpeechPlan.Utterance> items, float speed, int pause,
            Consumer<String> error, Runnable done) {
        stop();
        int request = generation;
        sequenceItem(items, 0, speed, pause, error, done, request);
    }
    private void sequenceItem(java.util.List<TableSpeechPlan.Utterance> items, int index,
            float speed, int pause, Consumer<String> error, Runnable done, int request) {
        if (closed || generation != request)
            return;
        if (index >= items.size()) {
            done.run();
            return;
        }
        TableSpeechPlan.Utterance item = items.get(index);
        playSingle(item.text, item.language, speed, defaultVolume, error,
                ()
                        -> main.postDelayed(()
                                                    -> sequenceItem(items, index + 1, speed, pause,
                                                            error, done, request),
                                pause),
                request);
    }
    void prefetch(String text, String language) {
        if (closed || !activeId.isEmpty() || text.trim().isEmpty())
            return;
        Voice selected = voice(language);
        if (selected == null || selected.getQuality() < Voice.QUALITY_NORMAL)
            return;
        File file = cached(text, language, selected, defaultSpeed);
        String id = file.getName();
        if (file.length() > 0 || pending.containsKey(id))
            return;
        if (engine.setVoice(selected) != TextToSpeech.SUCCESS)
            return;
        File part = new File(file.getPath().replace(".wav", ".part"));
        pending.put(id, part);
        engine.setSpeechRate(defaultSpeed);
        engine.setPitch(1f);
        if (engine.synthesizeToFile(text, null, part, id) != TextToSpeech.SUCCESS) {
            pending.remove(id);
            part.delete();
        }
    }
    void stop() {
        generation++;
        activeError = null;
        activeDone = null;
        activeId = "";
        waitingPlay = null;
        if (player != null) {
            player.release();
            player = null;
        }
        engine.stop();
    }
    void close() {
        closed = true;
        stop();
        engine.shutdown();
        for (File file : pending.values())
            file.delete();
        pending.clear();
    }
}
