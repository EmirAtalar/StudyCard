package com.studycard.app;
import org.json.JSONArray;
import org.json.JSONObject;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

final class CardTransfer {
    static final String[] FIELDS={"deck_name","term","definition","part_of_speech","source_lang","target_lang","example_sentence","example_translation","phonetic","notes","is_favorite","status","ease_factor","interval_days","repetition_count","due_date","last_reviewed"};
    static String export(CardStore store,boolean csv) throws Exception {
        JSONArray cards=new JSONArray(); StringBuilder output=new StringBuilder("\ufeff");
        if(csv) output.append(String.join(",",FIELDS)).append("\r\n");
        for(JSONObject original:store.list("card")) {
            JSONObject card=new JSONObject(); JSONObject deck=store.get(original.optString("deck_uuid"));
            for(String field:FIELDS) card.put(field,field.equals("deck_name") ? (deck==null?"":deck.optString("name")) : original.opt(field));
            cards.put(card);
            if(csv) { for(int i=0;i<FIELDS.length;i++){if(i>0) output.append(',');output.append('"').append(card.optString(FIELDS[i],"").replace("\"","\"\"")).append('"');}output.append("\r\n"); }
        }
        if(csv) return output.toString();
        JSONObject backup=new JSONObject(); backup.put("version",2); backup.put("decks",new JSONArray(store.list("deck")));backup.put("cards",cards);return backup.toString(2);
    }
    static List<List<String>> csvRows(String text) {
        List<List<String>> result=new ArrayList<>(); List<String> row=new ArrayList<>();StringBuilder cell=new StringBuilder();boolean quoted=false;
        text=text.replaceFirst("^\ufeff","");
        int commas=0,semicolons=0,tabs=0;boolean inQuotes=false;
        for(int i=0;i<text.length();i++){char c=text.charAt(i);if(c=='"')inQuotes=!inQuotes;else if(!inQuotes){if(c=='\n'||c=='\r')break;if(c==',')commas++;if(c==';')semicolons++;if(c=='\t')tabs++;}}
        char delimiter=tabs>commas&&tabs>semicolons?'\t':semicolons>commas?';':',';
        for(int i=0;i<text.length();i++) {char c=text.charAt(i);
            if(c=='"') {if(quoted && i+1<text.length() && text.charAt(i+1)=='"'){cell.append('"');i++;}else quoted=!quoted;}
            else if(c==delimiter && !quoted){row.add(cell.toString());cell.setLength(0);}
            else if((c=='\n'||c=='\r') && !quoted){if(c=='\r' && i+1<text.length() && text.charAt(i+1)=='\n')i++;row.add(cell.toString());cell.setLength(0);result.add(row);row=new ArrayList<>();}
            else cell.append(c);
        }
        if(quoted) throw new IllegalArgumentException("Unsupported card backup.");
        if(cell.length()>0 || !row.isEmpty()){row.add(cell.toString());result.add(row);}return result;
    }
    static String value(JSONObject row,String key,String fallback){String value=row.optString(key,"").trim();return value.isEmpty()?fallback:value;}
    static int[] importData(CardStore store,String text,String defaultDeck,boolean csv,Map<String,String> languageCodes) throws Exception {
        if(store.get(defaultDeck)==null)throw new IllegalArgumentException("Please select a deck.");
        JSONArray cards=new JSONArray(),decks=new JSONArray();
        if(csv) {
            List<List<String>> rows=csvRows(text);if(rows.isEmpty())return new int[3];
            List<String> header=rows.get(0);Map<String,String> aliases=new HashMap<>();
            String[] old={"Deste","Kelime/Kalıp","Anlamı","Kelime Türü","Örnek Cümle","Örnek Çevirisi","Fonetik","Notlar","Durum"};String[] canonical={"deck_name","term","definition","part_of_speech","example_sentence","example_translation","phonetic","notes","status"};
            for(int i=0;i<old.length;i++) aliases.put(CardStore.wordKey(old[i]),canonical[i]);
            aliases.put("word","term");aliases.put("meaning","definition");aliases.put("kelime","term");aliases.put("anlam","definition");aliases.put("deck","deck_name");
            List<String> fields=new ArrayList<>();for(String value:header) fields.add(aliases.getOrDefault(CardStore.wordKey(value),CardStore.wordKey(value)));
            boolean hasHeader=fields.contains("term")&&fields.contains("definition");
            if(!hasHeader)fields=header.size()<=3?Arrays.asList("term","definition","example_sentence"):Arrays.asList(canonical);
            for(int i=hasHeader?1:0;i<rows.size();i++){JSONObject card=new JSONObject();List<String> row=rows.get(i);for(int j=0;j<Math.min(row.size(),fields.size());j++)card.put(fields.get(j),row.get(j));cards.put(card);}
        } else {
            JSONObject backup=new JSONObject(text.replaceFirst("^\ufeff",""));int version=backup.optInt("version",1);if(version!=1&&version!=2)throw new IllegalArgumentException("Unsupported card backup.");cards=backup.getJSONArray("cards");decks=backup.optJSONArray("decks");
            Map<String,String> legacy=new HashMap<>();if(decks!=null)for(int i=0;i<decks.length();i++){JSONObject deck=decks.getJSONObject(i);legacy.put(deck.optString("id"),deck.optString("name"));legacy.put(deck.optString("uuid"),deck.optString("name"));}
            for(int i=0;i<cards.length();i++){JSONObject card=cards.getJSONObject(i);if(!card.has("deck_name"))card.put("deck_name",legacy.getOrDefault(card.optString("deck_id",card.optString("deck_uuid")),""));}
        }
        Map<String,String> names=new HashMap<>();for(JSONObject deck:store.list("deck"))names.put(deck.optString("name"),deck.optString("uuid"));
        java.util.Set<String> known=new java.util.HashSet<>();
        for(JSONObject card:store.list("card"))known.add(CardStore.wordKey(card.optString("term"))+"\u0001"+languageCodes.getOrDefault(card.optString("source_lang","en"),card.optString("source_lang","en"))+"\u0001"+languageCodes.getOrDefault(card.optString("target_lang","tr"),card.optString("target_lang","tr")));
        int[] report={0,0,0}; android.database.sqlite.SQLiteDatabase db=store.getWritableDatabase();db.beginTransaction();
        try {
            if(decks!=null)for(int i=0;i<decks.length();i++){JSONObject info=decks.optJSONObject(i);if(info==null)continue;String name=info.optString("name");if(name.trim().isEmpty()||names.containsKey(name))continue;String id=store.createDeck(name,info.optString("description"));JSONObject saved=store.get(id);for(String key:new String[]{"color","icon"})if(info.has(key))saved.put(key,info.optString(key));store.save("deck",id,saved);names.put(name,id);}
            for(int i=0;i<cards.length();i++) {
                JSONObject incoming=cards.optJSONObject(i);if(incoming==null){report[2]++;continue;}
                String term=incoming.optString("term").trim(),definition=incoming.optString("definition").trim();if(term.isEmpty()||definition.isEmpty()||term.length()>500||definition.length()>5000){report[2]++;continue;}
                String rawSource=incoming.optString("source_lang","en"),rawTarget=incoming.optString("target_lang","tr");String source=languageCodes.getOrDefault(rawSource,rawSource.isEmpty()?"en":rawSource),target=languageCodes.getOrDefault(rawTarget,rawTarget.isEmpty()?"tr":rawTarget);boolean duplicate=false;
                String identity=CardStore.wordKey(term)+"\u0001"+source+"\u0001"+target;
                if(known.contains(identity)){report[1]++;continue;}
                String due=value(incoming,"due_date",LocalDate.now().toString()),status=value(incoming,"status","new");
                try{LocalDate.parse(due);if(!Arrays.asList("new","learning","mastered").contains(status))throw new Exception();Double.parseDouble(value(incoming,"ease_factor","2.5"));Integer.parseInt(value(incoming,"interval_days","0"));Integer.parseInt(value(incoming,"repetition_count","0"));}catch(Exception invalid){report[2]++;continue;}
                String name=incoming.optString("deck_name"),deckId=names.getOrDefault(name,defaultDeck);
                if(!name.isEmpty()&&!names.containsKey(name)){deckId=store.createDeck(name,"");names.put(name,deckId);if(decks!=null)for(int n=0;n<decks.length();n++){JSONObject info=decks.optJSONObject(n);if(info!=null&&name.equals(info.optString("name"))){JSONObject saved=store.get(deckId);for(String key:new String[]{"description","color","icon"})if(info.has(key))saved.put(key,info.optString(key));store.save("deck",deckId,saved);break;}}}
                JSONObject card=new JSONObject();for(String field:FIELDS)if(!field.equals("deck_name"))card.put(field,incoming.optString(field,""));
                card.put("term",term);card.put("definition",definition);card.put("part_of_speech",incoming.optString("part_of_speech","word").isEmpty()?"word":incoming.optString("part_of_speech"));card.put("last_reviewed",incoming.optString("last_reviewed").isEmpty()?JSONObject.NULL:incoming.optString("last_reviewed"));card.put("deck_uuid",deckId);card.put("source_lang",source);card.put("target_lang",target);card.put("due_date",due);card.put("status",status);
                card.put("is_favorite",Arrays.asList("1","true","yes").contains(incoming.optString("is_favorite").toLowerCase(java.util.Locale.ROOT))?1:0);
                card.put("ease_factor",Math.max(1.3,Math.min(5.,incoming.optDouble("ease_factor",2.5))));card.put("interval_days",Math.max(0,incoming.optInt("interval_days",0)));card.put("repetition_count",Math.max(0,incoming.optInt("repetition_count",0)));
                store.save("card",null,card);known.add(identity);report[0]++;
            }
            db.setTransactionSuccessful();
        } finally {db.endTransaction();}
        return report;
    }
    static String language(String value){switch(value){case "İngilizce":case "English":case "Englisch":case "Inglés":return "en";case "Türkçe":case "Turkish":case "Türkisch":case "Turco":return "tr";default:return value;}}
}
