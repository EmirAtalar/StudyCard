package com.studycard.app;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.Set;

/** Android-independent rules, shared by the designer preview and published games. */
final class GameEngine {
    static final String[] MODES = {"quiz", "matching", "typing", "audio_dictation",
            "audio_translation", "audio_quiz", "memory", "word_builder"};
    static final class Pair {
        final String prompt, answer, language, answerLanguage, cardId;
        Pair(String prompt, String answer, String language, String answerLanguage) {
            this(prompt, answer, language, answerLanguage, "");
        }
        Pair(String prompt, String answer, String language, String answerLanguage, String cardId) {
            this.prompt = prompt.trim();
            this.answer = answer.trim();
            this.language = language;
            this.answerLanguage = answerLanguage;
            this.cardId = cardId;
        }
    }
    static boolean board(String mode) {
        return mode.equals("matching") || mode.equals("memory");
    }
    static boolean choice(String mode) {
        return mode.equals("quiz") || mode.equals("audio_quiz");
    }
    static boolean audio(String mode) {
        return mode.startsWith("audio_");
    }
    static String normalize(String text, String language) {
        if ("tr".equals(language))
            text = text.replace('I', 'ı').replace('İ', 'i');
        return Normalizer.normalize(text, Normalizer.Form.NFC)
                .toLowerCase(Locale.ROOT)
                .replace("ß", "ss")
                .replace('’', '\'')
                .trim()
                .replaceAll("^[ .!?。！？]+|[ .!?。！？]+$", "")
                .replaceAll("\\s+", " ");
    }
    static List<Pair> validatePool(String mode, List<Pair> input) {
        if (!java.util.Arrays.asList(MODES).contains(mode))
            throw new IllegalArgumentException("Invalid game recipe.");
        LinkedHashMap<String, Pair> unique = new LinkedHashMap<>();
        for (Pair pair : input) {
            if (pair.prompt.isEmpty() || (pair.answer.isEmpty() && !mode.equals("audio_dictation")))
                continue;
            if (mode.equals("word_builder")
                    && pair.prompt.codePointCount(0, pair.prompt.length()) > 60)
                throw new IllegalArgumentException(
                        "Word builder supports words or short phrases up to 60 characters.");
            String key = normalize(pair.prompt, pair.language);
            Pair previous = unique.get(key);
            if (previous != null && !mode.equals("audio_dictation")
                    && !normalize(previous.answer, previous.answerLanguage)
                            .equals(normalize(pair.answer, pair.answerLanguage)))
                throw new IllegalArgumentException(
                        "Some questions have multiple answers. Edit the source pairs to make each question unique.");
            if (previous == null)
                unique.put(key, pair);
        }
        List<Pair> result = new ArrayList<>(unique.values());
        Set<String> answers = new HashSet<>();
        for (Pair pair : result)
            answers.add(normalize(pair.answer, pair.answerLanguage));
        if (result.isEmpty())
            throw new IllegalArgumentException("Add complete question and answer pairs to start.");
        if ((board(mode) || choice(mode)) && answers.size() < 2)
            throw new IllegalArgumentException("This game needs at least two different answers.");
        if (board(mode) && answers.size() != result.size())
            throw new IllegalArgumentException(
                    "Matching needs a different answer for every question. Edit the source pairs.");
        return result;
    }
    final String mode;
    final List<Pair> pool, items;
    final Set<Integer> matched = new HashSet<>();
    final Random random;
    int index, correct, mistakes;
    boolean locked;
    GameEngine(String mode, List<Pair> pool, int count, boolean shuffle, Random random) {
        this.mode = mode;
        this.pool = validatePool(mode, pool);
        this.random = random;
        items = new ArrayList<>(this.pool);
        if (shuffle)
            Collections.shuffle(items, random);
        int limit = Math.min(items.size(), Math.min(Math.max(1, count), board(mode) ? 8 : 100));
        items.subList(limit, items.size()).clear();
    }
    boolean complete() {
        return board(mode) ? matched.size() == items.size() : index >= items.size();
    }
    Pair current() {
        return items.get(index);
    }
    String expected() {
        return mode.equals("audio_dictation") || mode.equals("word_builder") ? current().prompt
                                                                             : current().answer;
    }
    String expectedLanguage() {
        return mode.equals("audio_dictation") || mode.equals("word_builder")
                ? current().language
                : current().answerLanguage;
    }
    Boolean answer(String value) {
        if (complete() || locked)
            return null;
        String response = normalize(value, expectedLanguage()), expected = expected();
        boolean right = response.equals(normalize(expected, expectedLanguage()));
        if (!right && (mode.equals("typing") || mode.equals("audio_translation")))
            for (String alternative : expected.split("[,;/]"))
                if (!response.isEmpty()
                        && response.equals(normalize(alternative, expectedLanguage())))
                    right = true;
        locked = true;
        if (right)
            correct++;
        else
            mistakes++;
        return right;
    }
    void advance() {
        if (locked && !complete()) {
            index++;
            locked = false;
        }
    }
    Boolean match(int left, int right) {
        if (left < 0 || right < 0 || left >= items.size() || right >= items.size()
                || matched.contains(left) || matched.contains(right))
            return null;
        if (left == right) {
            matched.add(left);
            correct++;
            return true;
        }
        mistakes++;
        return false;
    }
    List<String> choices() {
        List<String> result = new ArrayList<>(), others = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        result.add(current().answer);
        seen.add(normalize(current().answer, current().answerLanguage));
        for (Pair pair : pool)
            if (seen.add(normalize(pair.answer, current().answerLanguage)))
                others.add(pair.answer);
        Collections.shuffle(others, random);
        result.addAll(others.subList(0, Math.min(3, others.size())));
        Collections.shuffle(result, random);
        return result;
    }
}
