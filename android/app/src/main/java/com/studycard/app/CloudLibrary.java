package com.studycard.app;

import org.json.JSONArray;
import org.json.JSONObject;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;

/** Shared v1 cloud library format. Field patches merge; tombstones never resurrect. */
final class CloudLibrary {
    private static final Set<String> DECK=new HashSet<>(Arrays.asList("name","description","icon","color","created_at"));
    private static final Set<String> CARD=new HashSet<>(Arrays.asList("deck_uuid","term","definition","part_of_speech","example_sentence","example_translation","phonetic","notes","target_lang","source_lang","status","is_favorite","repetition_count","interval_days","ease_factor","due_date","last_reviewed","created_at"));
    static JSONObject empty(long cursor) throws Exception {JSONObject response=new JSONObject();response.put("records",new JSONArray());response.put("acknowledged",new JSONArray());response.put("cursor",cursor);response.put("has_more",false);return response;}
    private static JSONObject unpack(JSONObject row) throws Exception {JSONObject record=new JSONObject(row.toString());record.put("data",new JSONObject(record.getString("data_json")));record.remove("data_json");return record;}
    private static void save(JSONObject state,JSONObject records,String entity,String id,JSONObject data,boolean deleted) throws Exception {
        long revision=state.getLong("revision")+1;state.put("revision",revision);JSONObject row=new JSONObject();row.put("entity",entity);row.put("uuid",id);row.put("revision",revision);row.put("deleted",deleted);row.put("data_json",data.toString());records.put(id,row);
    }
    private static void validate(String entity,JSONObject data,boolean full) throws Exception {
        Set<String> allowed=entity.equals("deck")?DECK:CARD;Iterator<String> keys=data.keys();
        while(keys.hasNext()){String key=keys.next();if(!allowed.contains(key))throw new Exception("Invalid cloud sync data.");Object value=data.opt(key);if(value instanceof String&&((String)value).length()>16000)throw new Exception("Invalid cloud sync data.");}
        for(String key:entity.equals("deck")?new String[]{"name"}:new String[]{"term","definition","deck_uuid"})if((full||data.has(key))&&(!(data.opt(key) instanceof String)||data.optString(key).trim().isEmpty()))throw new Exception("Invalid cloud sync data.");
        if(data.has("deck_uuid")&&!data.getString("deck_uuid").matches("[a-f0-9]{32}"))throw new Exception("Invalid cloud sync data.");
        if(data.has("status")&&!Arrays.asList("new","learning","mastered").contains(data.getString("status")))throw new Exception("Invalid cloud sync data.");
        if(data.has("due_date"))java.time.LocalDate.parse(data.getString("due_date"));
        if(data.has("ease_factor")&&(!Double.isFinite(data.getDouble("ease_factor"))||data.getDouble("ease_factor")<1.3||data.getDouble("ease_factor")>5))throw new Exception("Invalid cloud sync data.");
        for(String key:new String[]{"is_favorite","repetition_count","interval_days"})if(data.has(key)&&(!(data.opt(key) instanceof Number)||data.getDouble(key)!=data.getLong(key)||data.getLong(key)<0||(key.equals("is_favorite")&&data.getLong(key)>1)))throw new Exception("Invalid cloud sync data.");
    }
    static JSONObject merge(JSONObject state,JSONObject body) throws Exception {
        if(state.length()>0&&state.optInt("schema_version")!=1)throw new Exception("The cloud library format is not supported by this build.");
        state.put("schema_version",1);if(!state.has("revision"))state.put("revision",0);
        JSONObject records=state.optJSONObject("records");if(records==null){records=new JSONObject();state.put("records",records);}
        long cursor=body.getLong("cursor");JSONArray changes=body.getJSONArray("changes");if(cursor<0||changes.length()>500)throw new Exception("Invalid cloud sync data.");
        List<JSONObject> sorted=new ArrayList<>();for(int i=0;i<changes.length();i++)sorted.add(changes.getJSONObject(i));sorted.sort((a,b)->Integer.compare(a.optString("entity").equals("deck")?0:1,b.optString("entity").equals("deck")?0:1));
        for(JSONObject change:sorted) {
            String entity=change.getString("entity"),id=change.getString("uuid");if(!Arrays.asList("deck","card").contains(entity)||!id.matches("[a-f0-9]{32}"))throw new Exception("Invalid cloud sync data.");
            boolean deleted=change.optBoolean("deleted");JSONObject patch=change.getJSONObject("data");JSONObject old=records.has(id)?unpack(records.getJSONObject(id)):null;
            if(old!=null&&!old.getString("entity").equals(entity))throw new Exception("Invalid cloud sync data.");
            if(old!=null&&old.getBoolean("deleted"))continue;
            validate(entity,patch,false);JSONObject data=old==null?new JSONObject():new JSONObject(old.getJSONObject("data").toString());Iterator<String> keys=patch.keys();while(keys.hasNext()){String key=keys.next();data.put(key,patch.opt(key));}
            if(!deleted)validate(entity,data,true);
            if(entity.equals("card")&&!deleted){JSONObject parent=records.optJSONObject(data.getString("deck_uuid"));if(parent==null||!parent.optString("entity").equals("deck"))throw new Exception("The card deck could not sync. Please try again.");if(parent.getBoolean("deleted"))deleted=true;}
            if(old!=null&&old.getBoolean("deleted")==deleted&&old.getJSONObject("data").length()==data.length()&&CardStore.diff(data,old.getJSONObject("data")).length()==0)continue;
            save(state,records,entity,id,data,deleted);
            if(entity.equals("deck")&&deleted){List<String> children=new ArrayList<>();Iterator<String> ids=records.keys();while(ids.hasNext())children.add(ids.next());for(String child:children){JSONObject row=records.getJSONObject(child);if(row.getString("entity").equals("card")&&!row.getBoolean("deleted")){JSONObject childData=new JSONObject(row.getString("data_json"));if(id.equals(childData.optString("deck_uuid")))save(state,records,"card",child,childData,true);}}}
        }
        List<JSONObject> newer=new ArrayList<>();Iterator<String> ids=records.keys();while(ids.hasNext()){JSONObject row=records.getJSONObject(ids.next());if(row.getLong("revision")>cursor)newer.add(unpack(row));}newer.sort((a,b)->Long.compare(a.optLong("revision"),b.optLong("revision")));
        JSONObject response=empty(cursor);JSONArray page=response.getJSONArray("records"),ack=response.getJSONArray("acknowledged");for(int i=0;i<Math.min(500,newer.size());i++)page.put(newer.get(i));
        for(int i=0;i<changes.length();i++){String id=changes.getJSONObject(i).getString("uuid");if(records.has(id))ack.put(unpack(records.getJSONObject(id)));}
        response.put("cursor",page.length()>0?page.getJSONObject(page.length()-1).getLong("revision"):cursor);response.put("has_more",newer.size()>500);return response;
    }
}
