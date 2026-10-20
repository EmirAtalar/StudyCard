package com.studycard.app;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Stable IDs, muted cells and reading order are independent of visible positions. */
final class TableSpeechPlan {
    static final class Column {
        final String id, language;
        final int order;
        Column(String id, String language, int order) {
            this.id = id;
            this.language = language;
            this.order = order;
        }
    }
    static final class Row {
        final Map<String, String> cells;
        final Set<String> muted;
        Row(Map<String, String> cells, Set<String> muted) {
            this.cells = cells;
            this.muted = muted;
        }
    }
    static final class Utterance {
        final String text, language;
        Utterance(String text, String language) {
            this.text = text;
            this.language = language;
        }
    }
    static List<Utterance> create(
            List<Column> columns, List<Row> rows, boolean byColumns, int repeat) {
        List<Column> spoken = new ArrayList<>();
        for (Column column : columns)
            if (column.order > 0)
                spoken.add(column);
        spoken.sort(Comparator.comparingInt(column -> column.order));
        List<Utterance> onePass = new ArrayList<>();
        if (byColumns)
            for (Column column : spoken)
                for (Row row : rows)
                    add(onePass, column, row);
        else
            for (Row row : rows)
                for (Column column : spoken)
                    add(onePass, column, row);
        List<Utterance> result = new ArrayList<>();
        for (int i = 0; i < Math.max(1, Math.min(10, repeat)); i++)
            result.addAll(onePass);
        return result;
    }
    private static void add(List<Utterance> items, Column column, Row row) {
        String value = row.cells.getOrDefault(column.id, "").trim();
        if (!value.isEmpty() && !row.muted.contains(column.id))
            items.add(new Utterance(value, column.language));
    }
}
