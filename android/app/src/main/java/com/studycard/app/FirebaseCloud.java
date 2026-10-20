package com.studycard.app;

import android.content.Context;
import org.json.JSONObject;
import org.json.JSONTokener;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.Map;

/** Public project configuration and Firebase user-token REST requests. */
final class FirebaseCloud {
    private final JSONObject config;
    private static final int MAX_BYTES=32*1024*1024;
    FirebaseCloud(Context context) {
        JSONObject value;
        try(InputStream in=context.getAssets().open("firebase_config.json")){value=new JSONObject(SentenceExamples.read(in));}
        catch(Exception missing){value=new JSONObject();}
        config=value;
    }
    boolean ready(){try{validate();return true;}catch(Exception missing){return false;}}
    String webClientId(){return config.optString("webClientId");}
    private void validate() throws Exception {
        URI url=new URI(config.optString("databaseURL"));String host=url.getHost();
        if(!config.optString("projectId").matches("[a-z][a-z0-9-]{4,62}")||!config.optString("apiKey").matches("AIza[A-Za-z0-9_-]{30,}")
                ||!config.optString("webClientId").matches("[0-9]+-[A-Za-z0-9_-]+\\.apps\\.googleusercontent\\.com")
                ||!"https".equals(url.getScheme())||host==null||!host.matches("[a-z0-9.-]+\\.(firebaseio\\.com|firebasedatabase\\.app)")
                ||url.getUserInfo()!=null||url.getQuery()!=null||url.getFragment()!=null||url.getPort()!=-1
                ||(url.getPath()!=null&&!url.getPath().isEmpty()&&!url.getPath().equals("/")))
            throw new Exception("Google sign-in is not available in this build yet. Your offline cards are safe.");
    }
    static final class Conflict extends Exception {}
    static final class Response {final Object value;final String etag;Response(Object value,String etag){this.value=value;this.etag=etag;}}
    private static String encode(String value) throws Exception{return URLEncoder.encode(value,"UTF-8");}
    private Response request(String method,String url,String body,String type,Map<String,String> headers) throws Exception {
        HttpURLConnection connection=(HttpURLConnection)new URL(url).openConnection();
        connection.setInstanceFollowRedirects(false);connection.setRequestMethod(method);connection.setConnectTimeout(15000);connection.setReadTimeout(20000);
        for(Map.Entry<String,String> header:headers.entrySet())connection.setRequestProperty(header.getKey(),header.getValue());
        try {
            if(body!=null){byte[] data=body.getBytes(StandardCharsets.UTF_8);if(data.length>MAX_BYTES)throw new Exception("The cloud library is too large to sync in this build.");connection.setDoOutput(true);connection.setRequestProperty("Content-Type",type);connection.setFixedLengthStreamingMode(data.length);try(java.io.OutputStream out=connection.getOutputStream()){out.write(data);}}
            int status=connection.getResponseCode();if(status==412)throw new Conflict();
            if(status==401||status==403)throw new Exception("Cloud access was denied. Sign in again or check the project configuration.");
            if(status<200||status>=300)throw new Exception("Google could not complete the request. Please try again.");
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();
            try(InputStream in=connection.getInputStream()){byte[] buffer=new byte[8192];int count;while((count=in.read(buffer))!=-1){bytes.write(buffer,0,count);if(bytes.size()>MAX_BYTES)throw new Exception("The cloud library is too large to sync in this build.");}}
            return new Response(new JSONTokener(new String(bytes.toByteArray(),StandardCharsets.UTF_8)).nextValue(),connection.getHeaderField("ETag"));
        } catch(java.io.IOException error){throw new Exception("Cloud is unreachable. Your changes remain on this device and will be retried.");}
        finally{connection.disconnect();}
    }
    JSONObject signIn(String googleToken) throws Exception {
        validate();JSONObject body=new JSONObject();body.put("postBody","id_token="+encode(googleToken)+"&providerId=google.com");
        body.put("requestUri","https://"+config.getString("projectId")+".firebaseapp.com");body.put("returnSecureToken",true);
        JSONObject value=(JSONObject)request("POST","https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key="+config.getString("apiKey"),body.toString(),"application/json",Collections.emptyMap()).value;
        if(!"google.com".equals(value.optString("providerId"))||!value.optBoolean("emailVerified"))throw new Exception("Google could not complete the request. Please try again.");
        JSONObject session=new JSONObject();session.put("provider","firebase");session.put("server","firebase:"+config.getString("projectId"));session.put("user_id",value.getString("localId"));
        session.put("email",value.getString("email"));session.put("token",value.getString("idToken"));session.put("refresh_token",value.getString("refreshToken"));session.put("expires",System.currentTimeMillis()/1000+value.getLong("expiresIn"));return session;
    }
    JSONObject refresh(JSONObject session) throws Exception {
        validate();if(session.optLong("expires")>System.currentTimeMillis()/1000+60)return session;
        String body="grant_type=refresh_token&refresh_token="+encode(session.getString("refresh_token"));
        JSONObject value=(JSONObject)request("POST","https://securetoken.googleapis.com/v1/token?key="+config.getString("apiKey"),body,"application/x-www-form-urlencoded",Collections.emptyMap()).value;
        if(!session.getString("user_id").equals(value.optString("user_id")))throw new Exception("This library belongs to another Google account. Sign in with the original account.");
        JSONObject updated=new JSONObject(session.toString());updated.put("token",value.getString("id_token"));updated.put("refresh_token",value.getString("refresh_token"));updated.put("expires",System.currentTimeMillis()/1000+value.getLong("expires_in"));return updated;
    }
    JSONObject exchange(JSONObject session,JSONObject body) throws Exception {
        validate();String uid=session.getString("user_id");if(!uid.matches("[A-Za-z0-9_-]{1,128}")||!session.getString("server").equals("firebase:"+config.getString("projectId")))throw new Exception("This library belongs to another Google account. Sign in with the original account.");
        String root=config.getString("databaseURL").replaceAll("/+$","")+"/users/"+uid+"/library",auth="?auth="+encode(session.getString("token"));
        if(body.getJSONArray("changes").length()==0){Object revision=request("GET",root+"/revision.json"+auth,null,null,Collections.emptyMap()).value;long number=revision instanceof Number?((Number)revision).longValue():0;if(number==body.getLong("cursor"))return CloudLibrary.empty(number);}
        for(int attempt=0;attempt<5;attempt++) {
            Response previous=request("GET",root+".json"+auth,null,null,Collections.singletonMap("X-Firebase-ETag","true"));
            JSONObject snapshot=previous.value instanceof JSONObject?(JSONObject)previous.value:new JSONObject();long revision=snapshot.optLong("revision");
            JSONObject merged=CloudLibrary.merge(snapshot,body);
            if(snapshot.optLong("revision")==revision)return merged;
            if(previous.etag==null)throw new Exception("Google could not complete the request. Please try again.");
            try{request("PUT",root+".json"+auth,snapshot.toString(),"application/json",Collections.singletonMap("If-Match",previous.etag));return merged;}
            catch(Conflict conflict){}
        }
        throw new Exception("Cloud changes arrived during sync. Please retry.");
    }
}
