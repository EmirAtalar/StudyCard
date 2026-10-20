> Google/Firebase girişi ve bulut eşitleme güncel uygulama akışından kaldırıldı.
> Yeni kullanım: Ayarlar → Cihaz yedeği. Aşağıdaki bilgiler eski bulut protokolünün geliştirici referansıdır.

# Google hesabıyla PC ve Android eşitleme

Kullanıcı yalnızca **Google ile giriş yap** düğmesini kullanır. Sunucu adresi,
uygulamaya özel şifre veya ayrı hesap oluşturma ekranı yoktur. PC, sistem
tarayıcısında Google OAuth + PKCE ve geçici `127.0.0.1` geri dönüşü kullanır.
Android, Credential Manager hesap seçicisini kullanır. Her iki cihazın Google
kimliği aynı Firebase Authentication kullanıcısına dönüştürülür.

Kelimeler, desteler, favoriler ve tekrar ilerlemesi Firebase Realtime Database'de
hesaba özel alanda tutulur. ETag koşullu yazmaları aynı anda gelen değişiklikleri
yeniden birleştirir. Silinen kayıtların kimlikleri yeniden canlandırılmaz.
Değişiklik yokken yalnızca küçük sürüm değeri okunur; kütüphanenin tamamı indirilmez.
Yerel SQLite kütüphanesi internet yokken kullanılmaya devam eder.

## Geliştiricinin bir kez yapacağı kurulum

1. Bir Firebase projesi açın. Authentication → Sign-in method bölümünde Google'ı
   etkinleştirin. Bu proje için Realtime Database oluşturun.
2. Realtime Database → Rules bölümüne [database.rules.json](database.rules.json)
   içeriğini yayınlayın. Her kullanıcı yalnızca kendi UID alanını okuyabilir/yazabilir.
   CLI kullanıyorsanız bu dizinde `firebase deploy --only database --project PROJE_KIMLIGI`.
3. Android uygulamasını `com.studycard.app` paket adıyla ekleyin. Kullanılacak
   debug/release imza sertifikalarının SHA-1 izlerini kaydedin. Google girişini
   açtıktan sonra güncel `google-services.json` dosyasını indirin.
4. Aynı Google Cloud projesinde OAuth onay ekranını yapılandırın ve **Desktop app**
   türünde istemci oluşturup JSON dosyasını indirin. Test modunda kullanılacak
   Google hesaplarını test kullanıcılarına ekleyin.
5. [Boş yapılandırma örneğini](../duocards/data/firebase_config.example.json)
   kopyalayın ve Firebase web yapılandırmasındaki `projectId`, `apiKey`,
   `databaseURL` alanlarını doldurun. `databaseURL`, oluşturulan Realtime Database'in
   gerçek adresi olmalı; Firestore adresi kullanılamaz.
6. Proje kökünde çalıştırın:

```bash
python3 cloud/configure.py \
  --config /dosyalar/firebase-web.json \
  --desktop-client /dosyalar/oauth-desktop.json \
  --android-config /dosyalar/google-services.json
```

Bu komut iki platformun uygulama yapılandırmasını üretir. Android SDK için
`google-services` Gradle eklentisi gerekmez; kimlik doğrulaması Firebase REST ile
yapılır. OAuth Desktop istemcisinin Google tarafından verilen istemci sırrı varsa
yalnızca masaüstü yapılandırmasına eklenir. Servis hesabı veya yönetici özel anahtarı
uygulamaya eklenmez.

Boş yapılandırmada Google düğmesi devre dışıdır ve çevrimdışı kullanım devam eder.
Firebase projesi, OAuth istemcileri ve kurallar burada canlı olarak kurulmuş değildir.
Android SDK/gerçek cihaz ve canlı Google hesabıyla giriş henüz doğrulanmamıştır.

## Mevcut hesaplar ve sınırlar

Eski özel sunucu oturumu okunabilir. Aynı e-posta ile Google'a geçildiğinde yerel
kayıtlar ve kimlikler korunarak yeni buluta gönderilir. Başka hesaba bağlı kütüphane
farklı Google kullanıcısına yüklenmez. Eski hesaptan çıkılmış ve hesap e-postası
kaydedilmemişse önce eski hesapla giriş yapmak gerekir. Google'dan çıkış yerel
kartları silmez; yeniden girişte hesap bağlılığı korunur.

Bu sürümde değişiklik sırasında hesap kütüphanesi tek ETag işleminde birleştirilir.
Bulut kütüphanesi için uygulama sınırı 32 MiB'dir. Çok büyük kütüphanelerde aktarım
miktarı artar; Firebase'in güncel kota ve kullanım ücretleri proje sahibine aittir.
Proje kurulumu ücretli plana otomatik geçmez.

Resmî kaynaklar: [Firebase Google girişi](https://firebase.google.com/docs/auth/android/google-signin),
[Google masaüstü OAuth](https://developers.google.com/identity/protocols/oauth2/native-app),
[Firebase Auth REST](https://firebase.google.com/docs/reference/rest/auth),
[Realtime Database koşullu yazma](https://firebase.google.com/docs/database/rest/save-data).
