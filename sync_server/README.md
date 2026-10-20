# Study Card hesap ve eşitleme sunucusu

Python 3.10+ yeterlidir; ek Python paketi gerektirmez. PC ve Android bu servisi
kullanır. Şifreler rastgele tuzla scrypt üzerinden saklanır; oturum anahtarlarının
yalnızca SHA-256 özetleri sunucu veritabanına yazılır. Hesap verileri kullanıcı
kimliğiyle ayrılır. Şifreler ve kelimeler HTTP erişim kayıtlarına yazılmaz.

## Aynı Wi-Fi üzerinden kullanım

Proje klasöründe:

```bash
./start-sync-server.sh --host 0.0.0.0 --port 8765
```

Sunucu PC açıkken çalışır. PC'nin ağ ayarlarında görünen yerel IPv4 adresini
bulun. Örneğin `192.168.1.10` ise **her iki cihazda** sunucu adresini
`http://192.168.1.10:8765` yazın. Telefon ve PC aynı Wi-Fi'da olmalıdır; PC'nin
güvenlik duvarında yerel ağdan TCP 8765 erişimi açık olmalıdır.

PC'de **Ayarlar → Hesap ve cihazlar → Hesap oluştur** yolunu kullanın. Şifre
10–128 karakter olmalı. Android'de **Hesap → Giriş yap** üzerinden aynı
e-posta ve şifreyi kullanın. `http://192.168.1.10:8765/health` servis durumunu
JSON olarak gösterir.

## İnternet üzerinden kullanım

Projeyi sürekli açık bir Linux sunucusuna kopyalayın. Servisi localhost'ta
başlatıp Caddy ile HTTPS üzerinden yayınlayabilirsiniz:

```bash
./start-sync-server.sh --host 127.0.0.1 --port 8765
```

Örnek `/etc/caddy/Caddyfile` (alan adını kendi adresinizle değiştirin):

```caddy
study.example.com {
    reverse_proxy 127.0.0.1:8765
}
```

DNS adresini sunucuya yönlendirin; Caddy için 80/443 erişimini açın. Her iki
cihazda `https://study.example.com` adresini girin. Servis doğrudan TLS ile de
çalışabilir: `--cert fullchain.pem --key privkey.pem`.

Servisi yeniden başlatmalardan sonra çalıştırmak için örnek systemd ünitesi:

```ini
[Unit]
Description=Study Card synchronization
After=network.target

[Service]
Type=simple
User=studycard
WorkingDirectory=/srv/study-card
ExecStart=/usr/bin/python3 -m sync_server --host 127.0.0.1 --port 8765 --data-dir /var/lib/study-card
Restart=on-failure
UMask=0077
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

`studycard` kullanıcısını ve ona yazılabilir `/var/lib/study-card` klasörünü
oluşturun; dosyayı `/etc/systemd/system/study-card-sync.service` olarak
kaydedip `systemctl enable --now study-card-sync` ile başlatın. Bu örnekler
kurulum içindir; bu görev sırasında bir internet sunucusuna dağıtım yapılmadı.

## Eşitleme kuralları ve veriler

Desteler ve kartların bütün içerik alanları, favorileri, SRS durumları ve tekrar
tarihleri iki yönde aktarılır. Çalışma loglarının toplam istatistikleri,
zamanlayıcı kayıtları, eklenti ayarları ve cümle hafızası bu sürümde cihazda kalır.
Yerel kütüphane, ilk bağlandığı hesap/sunucu kimliğine sabitlenir; hesap değişimi
başka kişinin kelimelerini yanlışlıkla yüklememek için reddedilir. Çıkış yapmak
kelimeleri silmez. E-posta onayı ve şifre sıfırlama bu sürümde bulunmaz.

Her kayıt kalıcı bir UUID taşır. Yalnızca değişen alanlar gönderilir: PC'de anlam,
telefonda not değiştiyse ikisi birleşir. Aynı alan iki cihazda değişirse sunucuya
en son ulaşan değer geçerli olur. Sunucu bütün eski sürümleri `history` tablosunda
tutar. Silme UUID için kalıcıdır; çevrimdışı eski düzenleme silinen kartı geri
getirmez. Uzak silmeden etkilenen mevcut yerel içerik PC'de `sync_recovery`,
Android'de `recovery` tablosunda kurtarma amacıyla saklanır. Aynı adlı ayrı
desteler PC'de kısa kimlik ekiyle gösterilir.

Sunucu veritabanı varsayılan olarak `~/.local/share/study-card-server/accounts.db`
içindedir; `--data-dir` ile değiştirilebilir. Yedek alırken SQLite backup API
kullanılabilir:

```bash
python3 - <<'PY'
import sqlite3
from pathlib import Path
source = sqlite3.connect(Path.home() / '.local/share/study-card-server/accounts.db')
with sqlite3.connect('study-card-server-backup.db') as destination:
    source.backup(destination)
source.close()
PY
```

PC oturumu `~/.config/study-card/account.json` içinde, yalnızca sahibi tarafından
okunabilen izinlerle saklanır. Şifre kaydedilmez. Giriş denemeleri IP ve e-posta
başına dakikada on denemeyle sınırlıdır. Yönlendirmeler takip edilmez; yerel ağ
adresleri dışındaki HTTP adresleri istemciler tarafından reddedilir.

## Testler

```bash
./scripts/test.sh
```

`tests/test_account_sync.py`, farklı geçici cihaz veritabanlarını servis
mantığına bağlar. Soket erişimi olan ortamlarda HTTP istekleri de sınanır.
Android cihaz testleri ayrı çalıştırılır.

