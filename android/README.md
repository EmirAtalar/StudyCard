# Studycard Android

Android 8.0 ve üzeri için Java ile yazılmış yerel uygulama. Python, Qt, alan adı,
Google hesabı, Firebase yapılandırması veya ücretli servis gerekmez. Kartlar ve
çalışma verileri telefondaki SQLite veritabanında tutulur.

Masaüstündeki çalışma işlevleri mobil ekranlara uyarlandı:

- Aralıklı tekrar, kart çevirme, günlük hedef, favoriler, kart/deste düzenleme,
  kütüphane arama ve dil/durum/deste filtreleri; kütüphane quiz’i ve eşleştirme.
- Eklenti kur (yalnızca kalem simgesi), **32 simge**, tablo şablonları ve oyun stüdyosu.
  Satır/sütun adları, hücreler, sütun dili ve okuma sırası, sessiz hücreler,
  satır/sütun sırasıyla seslendirme, hız, ara verme ve tekrar ayarlanabilir.
  Tablo kopyalanabilir; hesap tablosundan sekmeyle ayrılmış satırlar yapıştırılabilir.
- **8 oyun:** çoktan seçmeli, eşleştirme, cevap yazma, dinleyip aynısını yazma,
  dinleyip çevirisini yazma, dinleyip şık seçme, hafıza kartları ve harf dizme.
  Elle girilmiş çiftler, kütüphane/deste veya özel tablo kaynak seçilebilir.
  Soru sayısı, süre, karıştırma, ipucu ve ses efektleri özelleştirilir.
  Ön izlemede puan kaydedilmez; kayıtlı oyunların sonuçları istatistiklere eklenir.
- **Eklentiler → Menüye ekle / Menüde aktif** ile Eklenti kur, ana menüler, dil
  paketleri ve kendi tablo/oyunlarını menüde açıp kapatma. Üstteki Menü düğmesi
  Eklentiler’e her zaman erişim verir; menüden kaldırmak verileri silmez.
- Yazarak Hatırla, Dinleme, Boşluk Doldurma, Taklit, Cümle Hafızası, Hatalarım,
  Favoriler ve günlük meydan okuma. Taklit havuzu arka planda hazırlanır.
- 15 dil paketi ile günlük phrasal verbs ve karıştırılan İngilizce kelimeler.
  Biçimler, anlamlar ve örnekler aranabilir ve sayfalanır; modüllerden kendi
  düzenlenebilir tablonu oluşturabilir veya kelimeleri destene ekleyebilirsin.
- Örnek cümle seçilince varsa çevirisi de kart formuna yazılır. Yerel örnekler
  ve çevrimiçi cümle araması; isteğe bağlı anlam/fonetik bulma düğmesi.
- İstatistikler: tekrar geçmişi, son 7 gün, çalışma serisi, pratik doğruluğu,
  oyun sonuçları, öğrenilen kelimeler ve odak süresi.
- Odak zamanlayıcısı / Pomodoro, kronometre, oturum notları ve saat hedefi.
  Zamanlayıcı uygulama arka plandayken süreyi korur; tamamlanan oturum kaydedilir.
- Aranabilir ayarlar: 3 koyu tema, 5 vurgu rengi, profil adı, yazı boyutu,
  azaltılmış animasyon, fonetik/not görünürlüğü, oturum büyüklüğü, ilerleme hızı,
  otomatik ses, seslendirme hızı/düzeyi, efektler, açılış sayfası, ekranı açık
  tutma ve günlük hatırlatıcı. Hazır çalışma profilleri yoktur; **Ayarları Kaydet**
  yumuşak yeşil arka planlıdır.
- Android ana ekran **Studycard widget’ı**: kelime, anlam, çalış ve sonraki kart.
  Telefonun ana ekranına uzun basıp Widget’lar bölümünden eklenir.
- Türkçe, İngilizce, Almanca ve İspanyolca arayüz; 76 kart dili.

Masaüstüne özgü sistem tepsisi, pencere kısayolları ve masaüstü widget’ı;
telefonda mobil menü, ekran seçenekleri, Android hatırlatıcıları ve ana ekran
widget’ıyla karşılanır. Android’in pil tasarrufu bildirimleri geciktirebilir;
uygulama açıkken zamanlayıcı kalan süreyi doğrudan hesaplar.

## Android Studio ile APK oluşturma

1. [Android Studio](https://developer.android.com/studio) kurun.
2. **Open** ile projenin **android** klasörünü açın. Üstteki Python proje
   klasörünü değil, `settings.gradle` bulunan klasörü seçin.
3. **SDK Manager** içinde **Android SDK Platform 35**, **Android SDK Build-Tools
   35.0.0** ve **Android SDK Platform-Tools** yükleyin. Emülatör kullanacaksanız
   Device Manager’dan ayrıca bir sanal cihaz kurun.
4. **Settings → Build, Execution, Deployment → Build Tools → Gradle → Gradle JDK**
   alanında **JDK 17** seçin. Kurulu değilse bu alandan 17 indirin. Gradle
   eşitlemesini tamamlayın; ilk eşitleme ve derleme internet gerektirir.
5. Android Studio Terminal’inde aşağıdaki komutu çalıştırın:

```bash
./gradlew assembleDebug
```

Windows’ta:

```bat
gradlew.bat assembleDebug
```

Terminal komutları da Java 17 kullanmalıdır; gerekiyorsa `JAVA_HOME` değerini
JDK 17 klasörüne ayarlayın. Linux’taki `build-apk.sh` yardımcısı kurulu JDK 17’yi
seçer. Android Studio SDK yolunu `android/local.properties` içine yazar. JDK 17 / Gradle
8.11.1 / SDK 35 / Build Tools 35.0.0 bu projedeki AGP 8.9.2 sürümüyle uyumludur.
[Resmî uyumluluk tablosu](https://developer.android.com/build/releases/agp-8-9-0-release-notes).

APK dosyası:

```text
android/app/build/outputs/apk/debug/app-debug.apk
```

Bu debug APK otomatik imzalanır ve kendi telefonunda denenebilir. Dosyayı telefona
kopyalayıp açın; telefon isterse dosyayı açtığınız uygulamaya bilinmeyen uygulama
kurma izni verin. USB hata ayıklama açık bir telefon bağlıysa:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

[Resmî komut satırı derleme rehberi](https://developer.android.com/build/building-cmdline).

Linux’ta SDK kurulumundan sonra yardımcı betik kullanılabilir:

```bash
cd android
./build-apk.sh
```

Yardımcı JDK 17 ve SDK ayarını kontrol eder, debug APK oluşturur ve dosya yolunu
çıktıda gösterir. SDK yolu terminalde `ANDROID_HOME` ile de belirtilebilir.

## Paylaşılacak imzalı APK

**Build → Generate Signed App Bundle or APK → APK** seçin. **Create new** ile
keystore oluşturun; anahtar adı ve şifreleri belirleyin, **release** seçip
oluşturun. Sonraki güncellemeleri **aynı keystore ve anahtarla** imzalayın.
Keystore ve şifrelerini güvenli bir yerde saklayın; uygulama güncellemeleri
aynı imzayı gerektirir. Keystore dosyaları Git’e eklenmez.

Android Studio sürümüne göre çıktı `app/release/` veya
`app/build/outputs/apk/release/` altında gösterilir; tamamlanma bildirimindeki
**Locate** bağlantısı kesin konumu açar. [Resmî imzalama rehberi](https://developer.android.com/studio/publish/app-signing).

`assembleRelease` tek başına imza ayarı olmadığında imzasız APK üretir; telefona
kurmak için yukarıdaki imzalama sihirbazını kullanın. APK’yı doğrudan paylaşmak
alan adı veya mağaza hesabı gerektirmez.

## Cihaz yedeği ve PC ile aktarım

**Ayarlar → Cihaza aktar** veya **İçe / dışa aktar → Cihaza aktar** tam Android
JSON yedeği oluşturur: kütüphane, boş desteler, tekrar ilerlemesi, favoriler,
istatistik/geçmiş, zamanlayıcı oturumları, cümle hafızası, tablo/oyunlar,
menü görünürlüğü ve ayarlar birlikte kaydedilir. Hesap ve erişim tokenları
çıktıya eklenmez. Dosya silinmedikçe başka bir telefonda da yüklenebilir.

**Cihaz yedeğini yükle**, hem Android JSON yedeğini hem masaüstünün **.studycard**
dosyasını tanır. Dosya, veritabanı, kayıtlar ve tercihler önce doğrulanır.
Yükleme mevcut verileri değiştirir; uygulamanın özel `files/backups` dizininde
önce kurtarma kopyası oluşturulur. SQLite işlemi başarısızsa eski kayıtlar korunur.

Telefondaki verileri PC’ye geri götürmek için **Masaüstüne aktar (.studycard)**
seçeneğini kullanın. Bu dosya masaüstündeki Cihaz yedeği bölümünden yüklenir.
Kütüphane, tekrar/pratik/zamanlayıcı geçmişi, cümleler, oyun sonuçları, tablolar,
oyunlar ve uygun ayarlar taşınır. Deste kimlikleri ve tablo sütun bağlantıları
platformlar arasında dönüştürülür. Aktarım bütün kütüphaneyi değiştirir;
CSV/JSON **kart aktarımı** ise ekleme yapar ve yinelenen kartları atlar.

## Doğrulama

SDK olmadan çalıştırılabilen oyun ve tablo ses planı testleri:

```bash
./tools/check-models.sh
```

63 kontrol, sekiz oyun türünün puanlama, tekrar cevap vermeyi engelleme,
Türkçe/Unicode yanıtlar, belirsiz sorular, eşleştirme sınırları ve tablo okuma
sırası/sessiz hücre/tekrar davranışını doğrular. Masaüstü testlerinde mobil
`.studycard` veritabanı şemasının açılması ve silme ilişkileri de doğrulanır.

SDK ve bağlı telefon veya açık emülatör ile:

```bash
./gradlew assembleDebug connectedDebugAndroidTest
```

Cihaz testleri ayrı veritabanlarında yerel yedek geri yükleme, bozuk yedeğin
reddi, masaüstü ZIP dönüşümü, sütun adları değişse de oyun kaynaklarının korunması
ve tokenların dışa aktarılmamasını sınar.

APK derlemesinden sonra tablo düzenleme, oyunlar, yedek yükleme, ses,
ekran döndürme, zamanlayıcı ve widget işlevlerini emülatörde veya telefonda deneyin.

Gradle Wrapper 8.11.1 dağıtımını SHA-256 ile doğrular. Dahil edilen launcher JAR
resmî Gradle 8.8 wrapper JAR’ıdır ve 8.11.1 dağıtımını başlatır.
