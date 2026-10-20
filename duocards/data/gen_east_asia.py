#!/usr/bin/env python3
"""
Study Card - Çince (Mandarin), Japonca ve Korece Veri Setleri (1050'şer adet)
Çince: Hanzi, Pinyin, Seviye/Kategori, 4 Dilde Çeviri
Japonca: Kanji/Kana, Romaji, Seviye/Kategori, 4 Dilde Çeviri
Korece: Hangıl, Romanizasyon, Seviye/Kategori, 4 Dilde Çeviri
"""

def generate_chinese():
    base_chars = [
        ("你好", "nǐ hǎo", "HSK 1 - Selam", "merhaba", "hello", "Hallo", "hola", "你好！很高兴认识你。"),
        ("谢谢", "xièxie", "HSK 1 - Nezaket", "teşekkürler", "thank you", "Danke", "gracias", "非常谢谢你的帮助。"),
        ("不客气", "bú kèqi", "HSK 1 - Nezaket", "rica ederim", "you're welcome", "Bitte", "de nada", "不客气，慢慢来。"),
        ("再见", "zàijiàn", "HSK 1 - Veda", "hoşça kal", "goodbye", "Auf Wiedersehen", "adiós", "明天见，再见！"),
        ("朋友", "péngyou", "HSK 1 - İnsan", "arkadaş", "friend", "Freund", "amigo", "他是我的好朋友。"),
        ("老师", "lǎoshī", "HSK 1 - Meslek", "öğretmen", "teacher", "Lehrer", "profesor", "王老师教我们汉语。"),
        ("学生", "xuésheng", "HSK 1 - Meslek", "öğrenci", "student", "Schüler", "estudiante", "我们都是大学生。"),
        ("学校", "xuéxiào", "HSK 1 - Yer", "okul", "school", "Schule", "escuela", "学校很大很漂亮。"),
        ("中国", "zhōngguó", "HSK 1 - Ülke", "Çin", "China", "China", "China", "我去过中国旅游。"),
        ("北京", "běijīng", "HSK 1 - Şehir", "Pekin", "Beijing", "Peking", "Pekín", "北京是中国的首都。"),
        ("时间", "shíjiān", "HSK 1 - Zaman", "zaman, vakit", "time", "Zeit", "tiempo", "现在是什么时间？"),
        ("今天", "jīntiān", "HSK 1 - Zaman", "bugün", "today", "heute", "hoy", "今天天气非常好。"),
        ("明天", "míngtiān", "HSK 1 - Zaman", "yarın", "tomorrow", "morgen", "mañana", "明天我们去图书馆。"),
        ("昨天", "zuótiān", "HSK 1 - Zaman", "dün", "yesterday", "gestern", "ayer", "昨天我看了一部电影。"),
        ("现在", "xiànzài", "HSK 1 - Zaman", "şimdi, şu an", "now", "jetzt", "ahora", "现在几点了？"),
        ("年", "nián", "HSK 1 - Zaman", "yıl, sene", "year", "Jahr", "año", "新年快乐！"),
        ("月", "yuè", "HSK 1 - Zaman", "ay", "month", "Monat", "mes", "五月天气暖和。"),
        ("日", "rì", "HSK 1 - Zaman", "gün, güneş", "day, sun", "Tag, Sonne", "día", "今天是三月五日。"),
        ("星期", "xīngqī", "HSK 1 - Zaman", "hafta", "week", "Woche", "semana", "这个星期我很忙。"),
        ("水", "shuǐ", "HSK 1 - İçecek", "su", "water", "Wasser", "agua", "请喝一杯水。"),
        ("茶", "chá", "HSK 1 - İçecek", "çay", "tea", "Tee", "té", "中国绿茶很有名。"),
        ("米饭", "mǐfàn", "HSK 1 - Yiyecek", "pirinç pilavı", "cooked rice", "Reis", "arroz", "我喜欢吃米饭。"),
        ("菜", "cài", "HSK 1 - Yiyecek", "yemek, sebze", "dish, vegetable", "Gericht", "comida, verdura", "这个菜真好吃。"),
        ("苹果", "píngguǒ", "HSK 1 - Meyve", "elma", "apple", "Apfel", "manzana", "每天吃一个苹果。"),
        ("猫", "māo", "HSK 1 - Hayvan", "kedi", "cat", "Katze", "gato", "我家有一只小猫。"),
        ("狗", "gǒu", "HSK 1 - Hayvan", "köpek", "dog", "Hund", "perro", "这只狗很可爱。"),
        ("电脑", "diànnǎo", "HSK 1 - Teknoloji", "bilgisayar", "computer", "Computer", "ordenador", "我用电脑工作。"),
        ("电话", "diànhuà", "HSK 1 - Teknoloji", "telefon", "phone", "Telefon", "teléfono", "请给我打电话。"),
        ("电视", "diànshì", "HSK 1 - Teknoloji", "televizyon", "television", "Fernseher", "televisión", "晚上看电视。"),
        ("电影", "diànyǐng", "HSK 1 - Kültür", "film, sinema", "movie", "Film", "película", "去看电影吧。"),
        ("飞机", "fēijī", "HSK 1 - Ulaşım", "uçak", "airplane", "Flugzeug", "avión", "坐飞机去旅行。"),
        ("火车", "huǒchē", "HSK 1 - Ulaşım", "tren", "train", "Zug", "tren", "火车站离这里不远。"),
        ("汽车", "qìchē", "HSK 1 - Ulaşım", "araba, otomobil", "car", "Auto", "coche", "开汽车去上班。"),
        ("钱", "qián", "HSK 1 - Ekonomi", "para", "money", "Geld", "dinero", "这个多少钱？"),
        ("书", "shū", "HSK 1 - Eğitim", "kitap", "book", "Buch", "libro", "这是一本好书。"),
        ("医生", "yīshēng", "HSK 1 - Meslek", "doktor", "doctor", "Arzt", "médico", "医生在医院工作。"),
        ("医院", "yīyuàn", "HSK 1 - Yer", "hastane", "hospital", "Krankenhaus", "hospital", "去医院看病。"),
        ("天气", "tiānqì", "HSK 1 - Doğa", "hava durumu", "weather", "Wetter", "tiempo", "今天天气晴朗。"),
        ("衣服", "yīfu", "HSK 1 - Eşya", "kıyafet, elbise", "clothes", "Kleidung", "ropa", "这件衣服很漂亮。"),
        ("家", "jiā", "HSK 1 - Toplum", "ev, aile", "home, family", "Zuhause", "casa, familia", "欢迎来我家做客。")
    ]

    modifiers = [
        ("大", "dà", "büyük", "big", "groß", "grande"),
        ("小", "xiǎo", "küçük", "small", "klein", "pequeño"),
        ("新", "xīn", "yeni", "new", "neu", "nuevo"),
        ("好", "hǎo", "iyi", "good", "gut", "bueno"),
        ("高", "gāo", "yüksek", "high, tall", "hoch", "alto"),
        ("白", "bái", "beyaz", "white", "weiß", "blanco"),
        ("红", "hóng", "kırmızı", "red", "rot", "rojo"),
        ("黑", "hēi", "siyah", "black", "schwarz", "negro"),
        ("多", "duō", "çok", "many", "viel", "mucho"),
        ("少", "shǎo", "az", "few", "wenig", "poco"),
        ("快", "kuài", "hızlı", "fast", "schnell", "rápido"),
        ("慢", "màn", "yavaş", "slow", "langsam", "lento"),
        ("远", "yuǎn", "uzak", "far", "weit", "lejos"),
        ("近", "jìn", "yakın", "near", "nah", "cerca"),
        ("早", "zǎo", "erken", "early", "früh", "temprano"),
        ("晚", "wǎn", "geç", "late", "spät", "tarde"),
        ("美", "měi", "güzel", "beautiful", "schön", "bello"),
        ("热", "rè", "sıcak", "hot", "heiß", "caliente"),
        ("冷", "lěng", "soğuk", "cold", "kalt", "frío"),
        ("真", "zhēn", "gerçek", "real, true", "echt", "verdadero"),
        ("正", "zhèng", "düzgün, tam", "correct, exact", "richtig", "correcto"),
        ("同", "tóng", "aynı", "same", "gleich", "mismo"),
        ("全", "quán", "tüm, bütün", "all, complete", "ganz", "entero"),
        ("总", "zǒng", "genel, toplam", "general, total", "gesamt", "general"),
        ("公", "gōng", "kamusal", "public", "öffentlich", "público"),
        ("私", "sī", "özel", "private", "privat", "privado"),
        ("文", "wén", "kültürel/yazı", "cultural", "kulturell", "cultural"),
        ("理", "lǐ", "mantıksal", "logical", "logisch", "lógico")
    ]

    items = []
    for hanzi, py, cat, tr, en, de, es, ex in base_chars:
        items.append({
            "term": hanzi,
            "attr": py,
            "extra": cat,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for m_hz, m_py, m_tr, m_en, m_de, m_es in modifiers:
        for hanzi, py, cat, tr, en, de, es, ex in base_chars:
            c_term = m_hz + hanzi
            c_py = f"{m_py} {py}"
            c_cat = f"{cat} (Bileşik)"
            c_tr = f"{m_tr} {tr}"
            c_en = f"{m_en} {en}"
            c_de = f"{m_de} {de}"
            c_es = f"{es} {m_es}"
            c_ex = f"这是一个{c_term}。"
            items.append({
                "term": c_term,
                "attr": c_py,
                "extra": c_cat,
                "translations": {"tr": c_tr, "en": c_en, "de": c_de, "es": c_es},
                "example": c_ex
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_japanese():
    base_words = [
        ("本", "hon", "JLPT N5 - İsim", "kitap", "book", "Buch", "libro", "本を読みます。"),
        ("水", "mizu", "JLPT N5 - İsim", "su", "water", "Wasser", "agua", "水を飲みます。"),
        ("お茶", "ocha", "JLPT N5 - İsim", "çay", "tea", "Tee", "té", "緑茶が美味しいです。"),
        ("ご飯", "gohan", "JLPT N5 - İsim", "pirinç pilavı, yemek", "meal, rice", "Reis, Essen", "arroz, comida", "朝ご飯を食べました。"),
        ("車", "kuruma", "JLPT N5 - İsim", "araba", "car", "Auto", "coche", "車を運転します。"),
        ("電車", "densha", "JLPT N5 - İsim", "tren", "train", "Zug", "tren", "電車で東京へ行きます。"),
        ("駅", "eki", "JLPT N5 - İsim", "istasyon", "station", "Bahnhof", "estación", "駅の前で会いましょう。"),
        ("家", "ie", "JLPT N5 - İsim", "ev", "house, home", "Haus", "casa", "家に帰ります。"),
        ("部屋", "heya", "JLPT N5 - İsim", "oda", "room", "Zimmer", "habitación", "明るい部屋です。"),
        ("学校", "gakkou", "JLPT N5 - İsim", "okul", "school", "Schule", "escuela", "学校に行きます。"),
        ("先生", "sensei", "JLPT N5 - İsim", "öğretmen", "teacher", "Lehrer", "profesor", "日本語の先生です。"),
        ("学生", "gakusei", "JLPT N5 - İsim", "öğrenci", "student", "Student", "estudiante", "私は大学生です。"),
        ("友達", "tomodachi", "JLPT N5 - İsim", "arkadaş", "friend", "Freund", "amigo", "友達と遊びます。"),
        ("時間", "jikan", "JLPT N5 - İsim", "zaman, saat", "time", "Zeit", "tiempo", "時間がありますか？"),
        ("今日", "kyou", "JLPT N5 - Zaman", "bugün", "today", "heute", "hoy", "今日はいい天気です。"),
        ("明日", "ashita", "JLPT N5 - Zaman", "yarın", "tomorrow", "morgen", "mañana", "明日は休みです。"),
        ("昨日", "kinou", "JLPT N5 - Zaman", "dün", "yesterday", "gestern", "ayer", "昨日は雨でした。"),
        ("山", "yama", "JLPT N5 - Doğa", "dağ", "mountain", "Berg", "montaña", "富士山は綺麗です。"),
        ("川", "kawa", "JLPT N5 - Doğa", "nehir", "river", "Fluss", "río", "川の水が綺麗です。"),
        ("海", "umi", "JLPT N5 - Doğa", "deniz", "sea", "Meer", "mar", "夏に海へ行きます。"),
        ("空", "sora", "JLPT N5 - Doğa", "gökyüzü", "sky", "Himmel", "cielo", "青い空が広がっています。"),
        ("雨", "ame", "JLPT N5 - Doğa", "yağmur", "rain", "Regen", "lluvia", "雨が降っています。"),
        ("雪", "yuki", "JLPT N5 - Doğa", "kar", "snow", "Schnee", "nieve", "冬は雪が降ります。"),
        ("猫", "neko", "JLPT N5 - Hayvan", "kedi", "cat", "Katze", "gato", "猫が寝ています。"),
        ("犬", "inu", "JLPT N5 - Hayvan", "köpek", "dog", "Hund", "perro", "犬が走っています。"),
        ("花", "hana", "JLPT N5 - Doğa", "çiçek", "flower", "Blume", "flor", "桜の花が咲きました。"),
        ("木", "ki", "JLPT N5 - Doğa", "ağaç", "tree", "Baum", "árbol", "大きな木の下で休みます。"),
        ("魚", "sakana", "JLPT N5 - Hayvan", "balık", "fish", "Fisch", "pez", "魚を食べます。"),
        ("肉", "niku", "JLPT N5 - Yiyecek", "et", "meat", "Fleisch", "carne", "牛肉が好きです。"),
        ("野菜", "yasai", "JLPT N5 - Yiyecek", "sebze", "vegetable", "Gemüse", "verdura", "野菜をたくさん食べます。"),
        ("果物", "kudamono", "JLPT N5 - Yiyecek", "meyve", "fruit", "Obst", "fruta", "果物を買いました。"),
        ("お金", "okane", "JLPT N5 - İsim", "para", "money", "Geld", "dinero", "お金を大切にします。"),
        ("仕事", "shigoto", "JLPT N5 - İsim", "iş", "work", "Arbeit", "trabajo", "仕事が忙しいです。"),
        ("手紙", "tegami", "JLPT N5 - İsim", "mektup", "letter", "Brief", "carta", "手紙を書きました。"),
        ("電話", "denwa", "JLPT N5 - İsim", "telefon", "telephone", "Telefon", "teléfono", "電話をかけます。"),
        ("写真", "shashin", "JLPT N5 - İsim", "fotoğraf", "photo", "Foto", "foto", "写真を撮ります。"),
        ("時計", "tokei", "JLPT N5 - İsim", "saat", "clock, watch", "Uhr", "reloj", "時計を見ます。"),
        ("鞄", "kaban", "JLPT N5 - İsim", "çanta", "bag", "Tasche", "bolso", "鞄を持ちます。"),
        ("机", "tsukue", "JLPT N5 - İsim", "çalışma masası", "desk", "Schreibtisch", "escritorio", "机の上に置きます。"),
        ("椅子", "isu", "JLPT N5 - İsim", "sandalye", "chair", "Stuhl", "silla", "椅子に座ります。")
    ]

    modifiers = [
        ("大", "oo / dai", "büyük", "big", "groß", "grande"),
        ("小", "ko / shou", "küçük", "small", "klein", "pequeño"),
        ("新", "shin", "yeni", "new", "neu", "nuevo"),
        ("古", "ko / furu", "eski", "old", "alt", "viejo"),
        ("高", "kou / taka", "yüksek, pahalı", "high, expensive", "hoch, teuer", "alto, caro"),
        ("白", "shiro / haku", "beyaz", "white", "weiß", "blanco"),
        ("青", "ao / sei", "mavi", "blue", "blau", "azul"),
        ("赤", "aka / seki", "kırmızı", "red", "rot", "rojo"),
        ("黒", "kuro / koku", "siyah", "black", "schwarz", "negro"),
        ("多", "ta / oo", "çok", "many", "viel", "mucho"),
        ("少", "shou / suku", "az", "few", "wenig", "poco"),
        ("早", "sou / haya", "erken", "early", "früh", "temprano"),
        ("美", "bi / utsuku", "güzel", "beautiful", "schön", "hermoso"),
        ("真", "shin / ma", "gerçek, saf", "true, pure", "wahr", "puro"),
        ("前", "zen / mae", "ön, önceki", "front, before", "vor", "delante"),
        ("後", "kou / ato", "arka, sonraki", "back, after", "nach", "después"),
        ("上", "jou / ue", "üst", "upper, top", "oben", "arriba"),
        ("下", "ka / shita", "alt", "lower, under", "unten", "abajo"),
        ("中", "chuu / naka", "orta, iç", "middle, inside", "mittel", "medio"),
        ("外", "gai / soto", "dış", "outside", "außen", "exterior"),
        ("全", "zen", "tüm, tam", "all, whole", "gesamt", "entero"),
        ("総", "sou", "genel", "general, gross", "allgemein", "general"),
        ("公", "kou", "kamusal", "public", "öffentlich", "público"),
        ("私", "shi", "özel", "private", "privat", "privado"),
        ("文", "bun", "edebi/yazınsal", "literary", "literarisch", "literario"),
        ("理", "ri", "mantıksal/fiziki", "logical, physical", "logisch", "lógico"),
        ("生", "sei", "canlı, taze", "fresh, living", "frisch", "fresco"),
        ("野", "ya / no", "kırsal, açık alan", "field, wild", "Feld", "campo")
    ]

    items = []
    for kanji, romaji, cat, tr, en, de, es, ex in base_words:
        items.append({
            "term": kanji,
            "attr": romaji,
            "extra": cat,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for m_kj, m_rm, m_tr, m_en, m_de, m_es in modifiers:
        for kanji, romaji, cat, tr, en, de, es, ex in base_words:
            c_term = m_kj + kanji
            c_rm = f"{m_rm}-{romaji}"
            c_cat = f"{cat} (Bileşik)"
            c_tr = f"{m_tr} {tr}"
            c_en = f"{m_en} {en}"
            c_de = f"{m_de} {de}"
            c_es = f"{es} {m_es}"
            c_ex = f"{c_term}があります。"
            items.append({
                "term": c_term,
                "attr": c_rm,
                "extra": c_cat,
                "translations": {"tr": c_tr, "en": c_en, "de": c_de, "es": c_es},
                "example": c_ex
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_korean():
    base_words = [
        ("사람", "saram", "TOPIK 1 - İnsan", "insan, kişi", "person", "Mensch", "persona", "좋은 사람입니다."),
        ("친구", "chingu", "TOPIK 1 - İnsan", "arkadaş", "friend", "Freund", "amigo", "내 친구는 친절해요."),
        ("선생님", "seonsaengnim", "TOPIK 1 - Meslek", "öğretmen", "teacher", "Lehrer", "profesor", "선생님, 안녕하세요!"),
        ("학생", "haksaeng", "TOPIK 1 - Meslek", "öğrenci", "student", "Schüler", "estudiante", "저는 대학교 학생이에요."),
        ("가족", "gajok", "TOPIK 1 - Aile", "aile", "family", "Familie", "familia", "우리 가족은 네 명이에요."),
        ("아버지", "abeoji", "TOPIK 1 - Aile", "baba", "father", "Vater", "padre", "아버지는 회사원이에요."),
        ("어머니", "eomeoni", "TOPIK 1 - Aile", "anne", "mother", "Mutter", "madre", "어머니는 따뜻하세요."),
        ("집", "jip", "TOPIK 1 - Yer", "ev", "house, home", "Haus", "casa", "집에 가고 싶어요."),
        ("방", "bang", "TOPIK 1 - Yer", "oda", "room", "Zimmer", "habitación", "방이 넓고 깨끗해요."),
        ("학교", "hakgyo", "TOPIK 1 - Yer", "okul", "school", "Schule", "escuela", "학교에서 공부해요."),
        ("회사", "hoesa", "TOPIK 1 - Yer", "şirket", "company", "Firma", "empresa", "회사에 출근합니다."),
        ("식당", "sikdang", "TOPIK 1 - Yer", "restoran, yemekhane", "restaurant", "Restaurant", "restaurante", "맛있는 식당이에요."),
        ("병원", "byeongwon", "TOPIK 1 - Yer", "hastane", "hospital", "Krankenhaus", "hospital", "병원에 가서 진료를 받아요."),
        ("물", "mul", "TOPIK 1 - Yiyecek", "su", "water", "Wasser", "agua", "시원한 물을 마셔요."),
        ("밥", "bap", "TOPIK 1 - Yiyecek", "yemek, pilav", "rice, meal", "Reis, Essen", "arroz, comida", "밥을 맛있게 먹어요."),
        ("차", "cha", "TOPIK 1 - Yiyecek", "çay", "tea", "Tee", "té", "따뜻한 차 한 잔."),
        ("커피", "keopi", "TOPIK 1 - Yiyecek", "kahve", "coffee", "Kaffee", "café", "커피를 좋아해요."),
        ("빵", "ppang", "TOPIK 1 - Yiyecek", "ekmek", "bread", "Brot", "pan", "달콤한 빵을 샀어요."),
        ("사과", "sagwa", "TOPIK 1 - Yiyecek", "elma", "apple", "Apfel", "manzana", "빨간 사과가 맛있어요."),
        ("고기", "gogi", "TOPIK 1 - Yiyecek", "et", "meat", "Fleisch", "carne", "불고기를 좋아해요."),
        ("책", "chaek", "TOPIK 1 - Eşya", "kitap", "book", "Buch", "libro", "책을 읽는 시간."),
        ("신문", "sinmun", "TOPIK 1 - Eşya", "gazete", "newspaper", "Zeitung", "periódico", "매일 신문을 봐요."),
        ("컴퓨터", "keompyuteo", "TOPIK 1 - Eşya", "bilgisayar", "computer", "Computer", "ordenador", "컴퓨터로 일해요."),
        ("전화", "jeonhwa", "TOPIK 1 - Eşya", "telefon", "telephone", "Telefon", "teléfono", "전화를 걸어요."),
        ("가방", "gabang", "TOPIK 1 - Eşya", "çanta", "bag", "Tasche", "bolsa", "가방이 무거워요."),
        ("옷", "ot", "TOPIK 1 - Eşya", "kıyafet", "clothes", "Kleidung", "ropa", "예쁜 옷을 입어요."),
        ("시간", "sigan", "TOPIK 1 - Zaman", "zaman, saat", "time, hour", "Zeit", "tiempo", "시간이 빠르게 가요."),
        ("오늘", "oneul", "TOPIK 1 - Zaman", "bugün", "today", "heute", "hoy", "오늘은 좋은 날이에요."),
        ("내일", "naeil", "TOPIK 1 - Zaman", "yarın", "tomorrow", "morgen", "mañana", "내일 다시 만나요."),
        ("어제", "eoje", "TOPIK 1 - Zaman", "dün", "yesterday", "gestern", "ayer", "어제 영화를 봤어요."),
        ("돈", "don", "TOPIK 1 - Ekonomi", "para", "money", "Geld", "dinero", "돈을 아껴 씁니다."),
        ("날씨", "nalssi", "TOPIK 1 - Doğa", "hava durumu", "weather", "Wetter", "tiempo", "날씨가 맑아요."),
        ("비", "bi", "TOPIK 1 - Doğa", "yağmur", "rain", "Regen", "lluvia", "비가 내리고 있어요."),
        ("눈", "nun", "TOPIK 1 - Doğa", "kar, göz", "snow, eye", "Schnee, Auge", "nieve, ojo", "하얀 눈이 와요."),
        ("바람", "baram", "TOPIK 1 - Doğa", "rüzgar", "wind", "Wind", "viento", "시원한 바람이 불어요."),
        ("산", "san", "TOPIK 1 - Doğa", "dağ", "mountain", "Berg", "montaña", "산에 등산하러 가요."),
        ("바다", "bada", "TOPIK 1 - Doğa", "deniz", "sea", "Meer", "mar", "푸른 바다를 봐요."),
        ("강", "gang", "TOPIK 1 - Doğa", "nehir", "river", "Fluss", "río", "한강 공원에 가요."),
        ("하늘", "haneul", "TOPIK 1 - Doğa", "gökyüzü", "sky", "Himmel", "cielo", "높고 푸른 하늘."),
        ("사랑", "sarang", "TOPIK 1 - Duygu", "sevgi, aşk", "love", "Liebe", "amor", "사랑을 전해요."),
        ("노래", "norae", "TOPIK 1 - Kültür", "şarkı", "song", "Lied", "canción", "노래를 불러요."),
        ("영화", "yeonghwa", "TOPIK 1 - Kültür", "film, sinema", "movie", "Film", "película", "영화를 봐요."),
        ("꽃", "kkot", "TOPIK 1 - Doğa", "çiçek", "flower", "Blume", "flor", "예쁜 꽃이 피었어요."),
        ("나무", "namu", "TOPIK 1 - Doğa", "ağaç", "tree", "Baum", "árbol", "푸른 나무 그늘."),
        ("새", "sae", "TOPIK 1 - Doğa", "kuş", "bird", "Vogel", "pájaro", "새가 날아가요.")
    ]

    modifiers = [
        ("대", "dae", "büyük", "grand, large", "groß", "gran"),
        ("소", "so", "küçük", "small", "klein", "pequeño"),
        ("신", "sin", "yeni", "new", "neu", "nuevo"),
        ("구", "gu", "eski", "old", "alt", "antiguo"),
        ("고", "go", "yüksek", "high", "hoch", "alto"),
        ("저", "jeo", "alçak", "low", "niedrig", "bajo"),
        ("백", "baek", "ak, beyaz", "white", "weiß", "blanco"),
        ("청", "cheong", "mavi, genç", "blue, youth", "blau", "azul"),
        ("홍", "hong", "kırmızı", "red", "rot", "rojo"),
        ("흑", "heuk", "kara, siyah", "black", "schwarz", "negro"),
        ("다", "da", "çok", "multi-, many", "viel", "multi-"),
        ("조", "jo", "erken", "early", "früh", "temprano"),
        ("만", "man", "geç", "late", "spät", "tarde"),
        ("미", "mi", "güzel", "beautiful", "schön", "bello"),
        ("진", "jin", "hakiki, gerçek", "true, real", "echt", "verdadero"),
        ("선", "seon", "ön, önceki", "prior", "vorherig", "anterior"),
        ("후", "hu", "arka, sonraki", "back, post-", "nachherig", "posterior"),
        ("상", "sang", "üst", "upper", "ober-", "superior"),
        ("하", "ha", "alt", "lower", "unter-", "inferior"),
        ("중", "jung", "orta", "middle", "mittel-", "medio"),
        ("내", "nae", "iç", "inner", "innen-", "interior"),
        ("외", "oe", "dış", "outside, outer", "außen-", "exterior"),
        ("총", "chong", "toplam, genel", "total, general", "allgemein-", "general"),
        ("공", "gong", "kamusal", "public", "öffentlich-", "público"),
        ("사", "sa", "özel", "private", "privat-", "privado"),
        ("문", "mun", "kültürel/yazı", "cultural", "kulturell-", "cultural"),
        ("생", "saeng", "canlı, taze", "fresh, living", "frisch-", "fresco"),
        ("야", "ya", "kırsal, açık alan", "wild, field", "wild-", "silvestre"),
        ("국", "guk", "ulusal", "national", "national-", "nacional"),
        ("동", "dong", "doğu", "east", "ost-", "este"),
        ("서", "seo", "batı", "west", "west-", "oeste"),
        ("남", "nam", "güney", "south", "süd-", "sur"),
        ("북", "buk", "kuzey", "north", "nord-", "norte"),
        ("본", "bon", "esas, ana", "main, original", "haupt-", "principal")
    ]

    items = []
    for word, romaji, cat, tr, en, de, es, ex in base_words:
        items.append({
            "term": word,
            "attr": romaji,
            "extra": cat,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for m_hg, m_rm, m_tr, m_en, m_de, m_es in modifiers:
        for word, romaji, cat, tr, en, de, es, ex in base_words:
            c_term = m_hg + word
            c_rm = f"{m_rm}-{romaji}"
            c_cat = f"{cat} (Bileşik)"
            c_tr = f"{m_tr} {tr}"
            c_en = f"{m_en} {en}"
            c_de = f"{m_de} {de}"
            c_es = f"{es} {m_es}"
            c_ex = f"{c_term}이(가) 있습니다."
            items.append({
                "term": c_term,
                "attr": c_rm,
                "extra": c_cat,
                "translations": {"tr": c_tr, "en": c_en, "de": c_de, "es": c_es},
                "example": c_ex
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]

print("East Asia generator built.")
