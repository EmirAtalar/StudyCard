package com.studycard.app;

import java.util.*;

/** Runs on a normal JDK without an Android SDK; throws on any failed rule. */
public final class ModelTests {
    private static int assertions;
    private static void check(boolean condition, String message) {
        assertions++;
        if (!condition)
            throw new AssertionError(message);
    }
    private static void rejects(Runnable action, String message) {
        try {
            action.run();
            throw new AssertionError(message);
        } catch (IllegalArgumentException expected) {
            assertions++;
        }
    }
    public static void main(String[] arguments) {
        List<GameEngine.Pair> pairs =
                Arrays.asList(new GameEngine.Pair("apple", "elma", "en", "tr"),
                        new GameEngine.Pair("book", "kitap", "en", "tr"),
                        new GameEngine.Pair("water", "su", "en", "tr"));
        for (String mode : GameEngine.MODES) {
            GameEngine session = new GameEngine(mode, pairs, 3, false, new Random(1));
            if (GameEngine.board(mode)) {
                check(!session.match(0, 1), mode + " rejects mismatches");
                check(session.match(0, 0), mode + " scores a pair");
                check(session.match(0, 0) == null, mode + " never scores a pair twice");
                check(session.match(1, 1), mode + " scores second pair");
                check(session.match(2, 2), mode + " scores last pair");
                check(session.complete() && session.correct == 3 && session.mistakes == 1,
                        mode + " completes correctly");
            } else {
                String expected = mode.equals("audio_dictation") || mode.equals("word_builder")
                        ? "apple"
                        : "elma";
                check(session.answer(expected), mode + " expected answer");
                check(session.answer(expected) == null && session.correct == 1,
                        mode + " locks scoring");
                session.advance();
                check(!session.answer("wrong"), mode + " incorrect answer");
                session.advance();
                check(session.answer(mode.equals("audio_dictation") || mode.equals("word_builder")
                                      ? "water"
                                      : "su"),
                        mode + " third answer");
                session.advance();
                check(session.complete() && session.correct == 2 && session.mistakes == 1,
                        mode + " results");
            }
        }
        GameEngine quiz = new GameEngine("quiz", pairs, 2, false, new Random(4));
        List<String> choices = quiz.choices();
        check(choices.contains("elma") && choices.size() == 3 && new HashSet<>(choices).size() == 3,
                "unique choices including right answer");
        GameEngine transcription = new GameEngine("audio_dictation",
                Arrays.asList(new GameEngine.Pair("hello world", "", "en", "tr")), 1, false,
                new Random());
        check(transcription.answer("HELLO WORLD!"), "dictation can omit meanings");
        GameEngine typing = new GameEngine("typing",
                Arrays.asList(new GameEngine.Pair("water", "su / içme suyu", "en", "tr")), 1, false,
                new Random());
        check(typing.answer("İÇME SUYU"), "Turkish alternatives");
        GameEngine exact = new GameEngine("audio_dictation",
                Arrays.asList(new GameEngine.Pair("one / two", "unused", "en", "tr")), 1, false,
                new Random());
        check(!exact.answer("one"), "transcription does not accept part of a phrase");
        check(GameEngine.normalize("IŞIK", "tr").equals("ışık"), "Turkish dotless I");
        check(GameEngine.normalize("İYİ", "tr").equals("iyi"), "Turkish dotted I");
        check(!GameEngine.normalize("año", "es").equals(GameEngine.normalize("ano", "es")),
                "meaningful accents are retained");
        check(GameEngine.normalize("Straße", "de").equals(GameEngine.normalize("STRASSE", "de")),
                "German case folding");
        check(GameEngine.normalize("Cafe\u0301", "fr").equals(GameEngine.normalize("Café", "fr")),
                "canonical Unicode");
        rejects(()
                        -> new GameEngine("quiz", Collections.singletonList(pairs.get(0)), 1, false,
                                new Random()),
                "choice games need two answers");
        rejects(()
                        -> GameEngine.validatePool("typing",
                                Arrays.asList(pairs.get(0),
                                        new GameEngine.Pair("APPLE", "armut", "en", "tr"))),
                "ambiguous questions rejected");
        rejects(()
                        -> GameEngine.validatePool("matching",
                                Arrays.asList(pairs.get(0),
                                        new GameEngine.Pair("pear", "elma", "en", "tr"))),
                "matching answers must be unique");
        check(GameEngine.validatePool("audio_dictation",
                                Arrays.asList(pairs.get(0),
                                        new GameEngine.Pair(
                                                "apple", "different meaning", "en", "tr")))
                                .size()
                        == 1,
                "dictation duplicates merge");
        rejects(()
                        -> GameEngine.validatePool("word_builder",
                                Collections.singletonList(new GameEngine.Pair(
                                        String.join("", Collections.nCopies(61, "x")), "long", "en",
                                        "tr"))),
                "letter games limit huge phrases");
        List<GameEngine.Pair> many = new ArrayList<>();
        for (int i = 0; i < 20; i++)
            many.add(new GameEngine.Pair("word " + i, "answer " + i, "en", "en"));
        check(new GameEngine("memory", many, 100, false, new Random()).items.size() == 8,
                "memory board limit");
        check(new GameEngine("typing", many, 4, false, new Random()).items.size() == 4,
                "configured question count");
        List<TableSpeechPlan.Column> columns =
                Arrays.asList(new TableSpeechPlan.Column("meaning", "tr", 0),
                        new TableSpeechPlan.Column("past", "en", 2),
                        new TableSpeechPlan.Column("word", "en", 1));
        Map<String, String> first = new HashMap<>();
        first.put("word", "go");
        first.put("past", "went");
        first.put("meaning", "gitmek");
        Map<String, String> second = new HashMap<>();
        second.put("word", "eat");
        second.put("past", "ate");
        List<TableSpeechPlan.Row> rows =
                Arrays.asList(new TableSpeechPlan.Row(first, Collections.emptySet()),
                        new TableSpeechPlan.Row(second, Collections.singleton("past")));
        List<TableSpeechPlan.Utterance> spoken = TableSpeechPlan.create(columns, rows, false, 1);
        check(spoken.size() == 3 && spoken.get(0).text.equals("go")
                        && spoken.get(1).text.equals("went") && spoken.get(2).text.equals("eat"),
                "row order, muted cells, silent columns");
        spoken = TableSpeechPlan.create(columns, rows, true, 2);
        check(spoken.size() == 6 && spoken.get(0).text.equals("go")
                        && spoken.get(1).text.equals("eat") && spoken.get(2).text.equals("went")
                        && spoken.get(3).text.equals("go"),
                "column order and repeats");
        check(TableSpeechPlan.create(columns, Collections.singletonList(rows.get(1)), false, 1)
                                .size()
                        == 1,
                "single-row reading");
        second.put("word", "  ");
        check(TableSpeechPlan.create(columns, rows, false, 1).size() == 2, "empty cells skipped");
        check(TableSpeechPlan
                        .create(Arrays.asList(new TableSpeechPlan.Column("past", "en", 1),
                                        new TableSpeechPlan.Column("word", "en", 1)),
                                Collections.singletonList(rows.get(0)), false, 1)
                        .get(0)
                        .text.equals("went"),
                "equal orders follow column positions");
        System.out.println("Mobile model tests passed: " + assertions
                + " assertions, all 8 game modes and table speech rules.");
    }
}
