package com.studycard.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** HTTPS client and encrypted session. Passwords are never stored. */
public final class SyncManager {
    private final CardStore store;
    private final SharedPreferences prefs;
    private final FirebaseCloud cloud;
    private volatile JSONObject session;
    private static final String ALIAS = "study-card-account-v1";

    public SyncManager(Context context, CardStore store) {
        this.store = store;
        cloud = new FirebaseCloud(context);
        prefs = context.getSharedPreferences("account", Context.MODE_PRIVATE);
        try {
            String blob = prefs.getString("session", "");
            if (blob.isEmpty()) session = new JSONObject();
            else {
                String[] parts = blob.split(":");
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
                session = new JSONObject(new String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), StandardCharsets.UTF_8));
            }
        } catch (Exception e) { session = new JSONObject(); prefs.edit().clear().commit(); }
    }

    private SecretKey key() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore"); ks.load(null);
        if (!ks.containsAlias(ALIAS)) {
            KeyGenerator gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            gen.init(new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
            gen.generateKey();
        }
        return (SecretKey)ks.getKey(ALIAS, null);
    }

    private void saveSession(JSONObject value) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, key());
        String blob = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + ":" + Base64.encodeToString(cipher.doFinal(value.toString().getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP);
        if (!prefs.edit().putString("session", blob).commit()) throw new Exception("Oturum cihazda kaydedilemedi.");
        session = value;
    }

    public boolean active() { return !session.optString("token").isEmpty(); }
    public String email() { return session.optString("email"); }
    public String server() { return session.optString("server"); }
    public boolean googleReady() { return cloud.ready(); }
    public String googleClientId() { return cloud.webClientId(); }

    public synchronized void loginGoogle(String googleToken) throws Exception {
        JSONObject account=cloud.signIn(googleToken);
        String binding=account.getString("server")+"|"+account.getString("user_id"),old=store.config("account","");
        String oldEmail=store.config("account_email",session.optString("email"));
        boolean migration=!old.isEmpty()&&!old.startsWith("firebase:")&&!oldEmail.isEmpty()&&oldEmail.equalsIgnoreCase(account.getString("email"));
        if(!old.isEmpty()&&!old.equals(binding)&&!migration)throw new Exception("This library belongs to another Google account. Sign in with the original account.");
        android.database.sqlite.SQLiteDatabase database=store.getWritableDatabase();database.beginTransaction();
        try {
            if(migration){store.configSet("previous_account",old);database.execSQL("UPDATE items SET baseline='{}',revision=0,dirty=1,generation=generation+1");store.configSet("cursor","0");}
            saveSession(account);store.configSet("account",binding);store.configSet("account_email",account.getString("email"));database.setTransactionSuccessful();
        } finally {database.endTransaction();}
    }

    public static String normalizeUrl(String value) throws Exception {
        value = value.trim().replaceAll("/+$", ""); URI uri;
        try { uri = new URI(value); } catch (Exception e) { throw new Exception("Sunucu adresini kontrol et."); }
        String host = uri.getHost();
        if (host == null || uri.getUserInfo() != null || uri.getQuery() != null || uri.getFragment() != null || (uri.getPath() != null && !uri.getPath().isEmpty()) || uri.getPort() > 65535)
            throw new Exception("Sunucu adresi https://sunucu.example veya http://192.168.1.10:8765 biçiminde olmalı.");
        boolean local = host.equals("localhost") || host.equals("[::1]") || host.equals("::1");
        if (host.matches("[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+")) {
            String[] p = host.split("\\."); int a = Integer.parseInt(p[0]), b = Integer.parseInt(p[1]);
            for (String n : p) if (Integer.parseInt(n) > 255) throw new Exception("Sunucu IP adresi geçersiz.");
            local = a == 127 || a == 10 || (a == 192 && b == 168) || (a == 172 && b >= 16 && b <= 31);
        }
        if (!"https".equals(uri.getScheme()) && !("http".equals(uri.getScheme()) && local))
            throw new Exception("İnternet sunucusu için HTTPS gerekir. HTTP yalnızca yerel ağda kullanılabilir.");
        return value;
    }

    static JSONObject request(String server, String path, JSONObject body, String token) throws Exception {
        HttpURLConnection conn = (HttpURLConnection)new URL(server + path).openConnection();
        conn.setInstanceFollowRedirects(false); conn.setRequestMethod("POST");
        conn.setConnectTimeout(15000); conn.setReadTimeout(20000); conn.setDoOutput(true);
        conn.setRequestProperty("Content-Type", "application/json");
        if (!token.isEmpty()) conn.setRequestProperty("Authorization", "Bearer " + token);
        byte[] data = body.toString().getBytes(StandardCharsets.UTF_8); conn.setFixedLengthStreamingMode(data.length);
        try {
            try (java.io.OutputStream out = conn.getOutputStream()) { out.write(data); }
            int status = conn.getResponseCode();
            InputStream stream = status >= 400 ? conn.getErrorStream() : conn.getInputStream();
            if (stream == null) throw new Exception("Sunucu yanıtı alınamadı.");
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (InputStream in = stream) { byte[] buffer = new byte[8192]; int read; while ((read = in.read(buffer)) != -1) { bytes.write(buffer, 0, read); if (bytes.size() > 32 * 1024 * 1024) throw new Exception("Sunucu yanıtı çok büyük."); } }
            if (status >= 300 && status < 400) throw new Exception("Sunucu yönlendirmesi kabul edilmedi; doğru HTTPS adresini kullan.");
            JSONObject result = new JSONObject(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
            if (status != 200) throw new Exception(result.optString("error", "Sunucu isteği reddetti."));
            return result;
        } catch (java.io.IOException e) { throw new Exception("Sunucuya ulaşılamadı. Kelimeler cihazda saklandı; yeniden denenecek."); }
        finally { conn.disconnect(); }
    }

    public synchronized void login(String server, String email, String password, boolean register) throws Exception {
        server = normalizeUrl(server);
        JSONObject body = new JSONObject(); CardStore.put(body, "email", email.trim()); CardStore.put(body, "password", password);
        JSONObject account = request(server, register ? "/v1/register" : "/v1/login", body, "");
        String binding = server + "|" + account.getString("user_id");
        String old = store.config("account", "");
        if (!old.isEmpty() && !old.equals(binding)) {
            try { request(server, "/v1/logout", new JSONObject(), account.getString("token")); } catch (Exception ignored) { }
            throw new Exception("Bu kütüphane başka hesaba bağlı. Aynı hesap ve sunucuyla giriş yap.");
        }
        CardStore.put(account, "server", server); saveSession(account); store.configSet("account", binding); store.configSet("account_email",account.getString("email"));
    }

    public synchronized void logout() throws Exception {
        JSONObject old = session;
        if (!prefs.edit().remove("session").commit()) throw new Exception("Çıkış cihazda kaydedilemedi.");
        session = new JSONObject();
        try { if (!old.optString("token").isEmpty()&&!old.optString("provider").equals("firebase")) request(old.getString("server"), "/v1/logout", new JSONObject(), old.getString("token")); } catch (Exception ignored) { }
    }

    public synchronized boolean sync() throws Exception {
        if (!active()) return false;
        boolean firebase=session.optString("provider").equals("firebase");
        if(firebase){JSONObject updated=cloud.refresh(session);if(updated!=session)saveSession(updated);}
        String url = firebase?server():normalizeUrl(server()), token = session.getString("token");
        if (!store.config("account", "").equals(url + "|" + session.getString("user_id"))) throw new Exception("Oturum bu kütüphaneye ait değil; yeniden giriş yap.");
        CardStore.Batch batch = store.batch(); long cursor = Long.parseLong(store.config("cursor", "0"));
        JSONObject body = new JSONObject(); CardStore.put(body, "cursor", cursor); CardStore.put(body, "changes", batch.changes);
        JSONObject response = firebase?cloud.exchange(session,body):request(url, "/v1/sync", body, token);
        Map<String, JSONObject> incoming = new LinkedHashMap<>();
        JSONArray ack = response.getJSONArray("acknowledged");
        for (int i = 0; i < ack.length(); i++) { JSONObject r = ack.getJSONObject(i); incoming.put(r.getString("uuid"), r); }
        for (int page = 0; ; page++) {
            JSONArray records = response.getJSONArray("records");
            for (int i = 0; i < records.length(); i++) {
                JSONObject r = records.getJSONObject(i), old = incoming.get(r.getString("uuid"));
                if (old == null || old.getLong("revision") <= r.getLong("revision")) incoming.put(r.getString("uuid"), r);
            }
            cursor = response.getLong("cursor");
            if (!response.getBoolean("has_more")) break;
            if (page >= 99) throw new Exception("Kütüphane çok büyük; yeniden eşitle.");
            CardStore.put(body, "cursor", cursor); CardStore.put(body, "changes", new JSONArray());
            response = firebase?cloud.exchange(session,body):request(url, "/v1/sync", body, token);
        }
        store.apply(incoming, batch, cursor); return !incoming.isEmpty();
    }
}
