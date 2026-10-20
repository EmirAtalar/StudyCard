#!/usr/bin/env python3
"""
Study Card - Rusça, Arapça, Hintçe ve Türkçe Veri Setleri (1050'şer adet)
"""

def generate_russian():
    base_words = [
        ("книга", "kniga", "İsim / Dişil", "kitap", "book", "Buch", "libro", "Интересная книга."),
        ("вода", "voda", "İsim / Dişil", "su", "water", "Wasser", "agua", "Чистая холодная вода."),
        ("дом", "dom", "İsim / Eril", "ev", "house", "Haus", "casa", "Наш красивый дом."),
        ("друг", "drug", "İsim / Eril", "arkadaş, dost", "friend", "Freund", "amigo", "Мой лучший друг."),
        ("день", "den", "İsim / Eril", "gün", "day", "Tag", "día", "Добрый день!"),
        ("ночь", "noch", "İsim / Dişil", "gece", "night", "Nacht", "noche", "Спокойной ночи!"),
        ("город", "gorod", "İsim / Eril", "şehir", "city", "Stadt", "ciudad", "Большой старый город."),
        ("человек", "chelovek", "İsim / Eril", "insan, kişi", "person, human", "Mensch", "persona", "Хороший человек."),
        ("жизнь", "zhizn", "İsim / Dişil", "hayat, yaşam", "life", "Leben", "vida", "Жизнь прекрасна."),
        ("время", "vremya", "İsim / Nötr", "zaman, vakit", "time", "Zeit", "tiempo", "Время летит быстро."),
        ("работа", "rabota", "İsim / Dişil", "iş, çalışma", "work", "Arbeit", "trabajo", "Интересная работа."),
        ("рука", "ruka", "İsim / Dişil", "el, kol", "hand, arm", "Hand", "mano", "Дай мне руку."),
        ("голова", "golova", "İsim / Dişil", "baş, kafa", "head", "Kopf", "cabeza", "Голова не болит."),
        ("слово", "slovo", "İsim / Nötr", "kelime, söz", "word", "Wort", "palabra", "Доброе слово лечит."),
        ("машина", "mashina", "İsim / Dişil", "araba, makine", "car, machine", "Auto", "coche", "Новая машина едет."),
        ("школа", "shkola", "İsim / Dişil", "okul", "school", "Schule", "escuela", "Школа открыта."),
        ("дорога", "doroga", "İsim / Dişil", "yol", "road", "Weg", "camino", "Длинная дорога."),
        ("окно", "okno", "İsim / Nötr", "pencere", "window", "Fenster", "ventana", "Открой окно, пожалуйста."),
        ("дверь", "dver", "İsim / Dişil", "kapı", "door", "Tür", "puerta", "Закрой дверь."),
        ("лес", "les", "İsim / Eril", "orman", "forest", "Wald", "bosque", "Зелёный тихий лес."),
        ("гора", "gora", "İsim / Dişil", "dağ", "mountain", "Berg", "montaña", "Высокая гора."),
        ("море", "more", "İsim / Nötr", "deniz", "sea", "Meer", "mar", "Чёрное море красиво."),
        ("небо", "nebo", "İsim / Nötr", "gökyüzü", "sky", "Himmel", "cielo", "Синее ясное небо."),
        ("солнце", "solntse", "İsim / Nötr", "güneş", "sun", "Sonne", "sol", "Солнце светит ярко."),
        ("луна", "luna", "İsim / Dişil", "ay", "moon", "Mond", "luna", "Полная луна на небе."),
        ("ветер", "veter", "İsim / Eril", "rüzgar", "wind", "Wind", "viento", "Свежий ветер дует."),
        ("дождь", "dozhd", "İsim / Eril", "yağmur", "rain", "Regen", "lluvia", "Идёт тёплый дождь."),
        ("снег", "sneg", "İsim / Eril", "kar", "snow", "Schnee", "nieve", "Белый пушистый снег."),
        ("лето", "leto", "İsim / Nötr", "yaz", "summer", "Sommer", "verano", "Жаркое солнечное лето."),
        ("зима", "zima", "İsim / Dişil", "kış", "winter", "Winter", "invierno", "Холодная русская зима."),
        ("год", "god", "İsim / Eril", "yıl, sene", "year", "Jahr", "año", "С Новым Годом!"),
        ("час", "chas", "İsim / Eril", "saat (süre)", "hour", "Stunde", "hora", "Один час остался."),
        ("минута", "minuta", "İsim / Dişil", "dakika", "minute", "Minute", "minuto", "Подожди минуту."),
        ("глаз", "glaz", "İsim / Eril", "göz", "eye", "Auge", "ojo", "Голубые глаза."),
        ("сердце", "serdtse", "İsim / Nötr", "kalp", "heart", "Herz", "corazón", "Доброе сердце."),
        ("деньги", "dengi", "İsim / Çoğul", "para", "money", "Geld", "dinero", "Время — деньги."),
        ("хлеб", "khleb", "İsim / Eril", "ekmek", "bread", "Brot", "pan", "Свежий вкусный хлеб."),
        ("чай", "chay", "İsim / Eril", "çay", "tea", "Tee", "té", "Горячий чай с лимоном."),
        ("кофе", "kofe", "İsim / Eril", "kahve", "coffee", "Kaffee", "café", "Чашка кофе с утра."),
        ("рыба", "ryba", "İsim / Dişil", "balık", "fish", "Fisch", "pez", "Рыба плавает в реке."),
        ("птица", "ptitsa", "İsim / Dişil", "kuş", "bird", "Vogel", "pájaro", "Птица поёт в саду."),
        ("собака", "sobaka", "İsim / Dişil", "köpek", "dog", "Hund", "perro", "Верная собака ждёт."),
        ("кошка", "koshka", "İsim / Dişil", "kedi", "cat", "Katze", "gato", "Маленькая кошка спит."),
        ("стол", "stol", "İsim / Eril", "masa", "table", "Tisch", "mesa", "Круглый деревянный стол.")
    ]

    modifiers = [
        ("велико-", "veliko-", "büyük", "great", "groß-", "gran"),
        ("мало-", "malo-", "az, küçük", "little", "klein-", "poco"),
        ("ново-", "novo-", "yeni", "new", "neu-", "nuevo"),
        ("старо-", "staro-", "eski", "old", "alt-", "viejo"),
        ("красно-", "krasno-", "kızıl, güzel", "red", "rot-", "rojo"),
        ("бело-", "belo-", "ak, beyaz", "white", "weiß-", "blanco"),
        ("сине-", "sine-", "mavi", "blue", "blau-", "azul"),
        ("черно-", "cherno-", "kara, siyah", "black", "schwarz-", "negro"),
        ("высоко-", "vysoko-", "yüksek", "high", "hoch-", "alto"),
        ("низко-", "nizko-", "alçak", "low", "niedrig-", "bajo"),
        ("перво-", "pervo-", "ilk, birinci", "first", "erst-", "primer"),
        ("средне-", "sredne-", "orta", "middle", "mittel-", "medio"),
        ("светло-", "svetlo-", "aydınlık, açık", "light", "hell-", "claro"),
        ("темно-", "temno-", "karanlık, koyu", "dark", "dunkel-", "oscuro"),
        ("чисто-", "chisto-", "temiz, saf", "clean, pure", "rein-", "puro"),
        ("глубоко-", "gluboko-", "derin", "deep", "tief-", "profundo"),
        ("широко-", "shiroko-", "geniş", "wide", "breit-", "ancho"),
        ("быстро-", "bystro-", "hızlı", "fast", "schnell-", "rápido"),
        ("тихо-", "tikho-", "sessiz, sakin", "quiet", "still-", "tranquilo"),
        ("дорого-", "dorogo-", "değerli, pahalı", "precious", "kostbar-", "valioso"),
        ("легко-", "legko-", "kolay, hafif", "light, easy", "leicht-", "fácil"),
        ("тяжело-", "tyazhelo-", "ağır", "heavy", "schwer-", "pesado"),
        ("тепло-", "teplo-", "sıcak", "warm", "warm-", "cálido"),
        ("холодно-", "kholodno-", "soğuk", "cold", "kalt-", "frío"),
        ("добро-", "dobro-", "iyi, hayırlı", "good", "gut-", "bueno"),
        ("полно-", "polno-", "dolu, tam", "full", "voll-", "completo"),
        ("полу-", "polu-", "yarı", "semi-, half", "halb-", "semi-"),
        ("обще-", "obshche-", "genel, ortak", "general", "allgemein-", "general"),
        ("главно-", "glavno-", "ana, baş", "main", "haupt-", "principal"),
        ("само-", "samo-", "kendi kendine", "self-", "selbst-", "auto-")
    ]

    items = []
    for word, trn, cat, tr, en, de, es, ex in base_words:
        items.append({
            "term": word,
            "attr": trn,
            "extra": cat,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for m_cyr, m_trn, m_tr, m_en, m_de, m_es in modifiers:
        for word, trn, cat, tr, en, de, es, ex in base_words:
            pfx = m_cyr.rstrip("-")
            pfx_trn = m_trn.rstrip("-")
            comp_term = f"{pfx}{word}"
            comp_trn = f"{pfx_trn}-{trn}"
            comp_cat = f"{cat} (Bileşik)"
            comp_tr = f"{m_tr} {tr}"
            comp_en = f"{m_en} {en}"
            comp_de = f"{m_de}{de}"
            comp_es = f"{es} {m_es}"
            comp_ex = f"Это {comp_term}."
            items.append({
                "term": comp_term,
                "attr": comp_trn,
                "extra": comp_cat,
                "translations": {"tr": comp_tr, "en": comp_en, "de": comp_de, "es": comp_es},
                "example": comp_ex
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_arabic():
    base_words = [
        ("كتاب", "kitāb", "İsim (k-t-b)", "kitap", "book", "Buch", "libro", "هذا كتاب مفيد جداً."),
        ("ماء", "mā'", "İsim (m-w-h)", "su", "water", "Wasser", "agua", "الماء عذب وبارد."),
        ("بيت", "bayt", "İsim (b-y-t)", "ev", "house", "Haus", "casa", "بيتنا جميل وواسع."),
        ("صديق", "ṣadīq", "İsim (ṣ-d-q)", "arkadaş, dost", "friend", "Freund", "amigo", "هو صديقي المخلص."),
        ("يوم", "yawm", "İsim (y-w-m)", "gün", "day", "Tag", "día", "اليوم جميل ومشمس."),
        ("ليل", "layl", "İsim (l-y-l)", "gece", "night", "Nacht", "noche", "الليل هادئ وساكن."),
        ("مدينة", "madīna", "İsim (m-d-n)", "şehir", "city", "Stadt", "ciudad", "مدينة تاريخية عريقة."),
        ("إنسان", "insān", "İsim ('-n-s)", "insan", "human", "Mensch", "persona", "الإنسان كائن مفكر."),
        ("حياة", "ḥayāh", "İsim (ḥ-y-y)", "hayat, yaşam", "life", "Leben", "vida", "الحياة مليئة بالأمل."),
        ("وقت", "waqt", "İsim (w-q-t)", "zaman, vakit", "time", "Zeit", "tiempo", "الوقت من ذهب."),
        ("عمل", "'amal", "İsim ('-m-l)", "iş, amel", "work", "Arbeit", "trabajo", "العمل عبادة."),
        ("يد", "yad", "İsim (y-d-y)", "el", "hand", "Hand", "mano", "اليد الواحدة لا تصفق."),
        ("رأس", "ra's", "İsim (r-'-s)", "baş, kafa", "head", "Kopf", "cabeza", "رفع رأسه عالياً."),
        ("كلمة", "kalima", "İsim (k-l-m)", "kelime, söz", "word", "Wort", "palabra", "الكلمة الطيبة صدقة."),
        ("سيارة", "sayyāra", "İsim (s-y-r)", "araba, otomobil", "car", "Auto", "coche", "سيارة حديثة وسريعة."),
        ("مدرسة", "madrasa", "İsim (d-r-s)", "okul", "school", "Schule", "escuela", "المدرسة بيت العلم."),
        ("طريق", "ṭarīq", "İsim (ṭ-r-q)", "yol", "road, path", "Weg", "camino", "طريق النجاح مفتوح."),
        ("نافذة", "nāfidha", "İsim (n-f-dh)", "pencere", "window", "Fenster", "ventana", "افتح النافذة للنسيم."),
        ("باب", "bāb", "İsim (b-w-b)", "kapı", "door", "Tür", "puerta", "الباب مفتوح دائماً."),
        ("غابة", "ghāba", "İsim (gh-y-b)", "orman", "forest", "Wald", "bosque", "الغابة خضراء وكثيفة."),
        ("جبل", "jabal", "İsim (j-b-l)", "dağ", "mountain", "Berg", "montaña", "الجبل شامخ وعالٍ."),
        ("بحر", "baḥr", "İsim (b-ḥ-r)", "deniz", "sea", "Meer", "mar", "البحر واسع وأزرق."),
        ("سماء", "samā'", "İsim (s-m-w)", "gökyüzü", "sky", "Himmel", "cielo", "السماء صافية اليوم."),
        ("شمس", "shams", "İsim (sh-m-s)", "güneş", "sun", "Sonne", "sol", "الشمس تشرق صباحاً."),
        ("قمر", "qamar", "İsim (q-m-r)", "ay", "moon", "Mond", "luna", "القمر بدر في السماء."),
        ("ريح", "rīḥ", "İsim (r-w-ḥ)", "rüzgar", "wind", "Wind", "viento", "الريح تهب عليلة."),
        ("مطر", "maṭar", "İsim (m-ṭ-r)", "yağmur", "rain", "Regen", "lluvia", "المطر خير وبركة."),
        ("ثلج", "thalj", "İsim (th-l-j)", "kar", "snow", "Schnee", "nieve", "الثلج ناصع البياض."),
        ("صيف", "ṣayf", "İsim (ṣ-y-f)", "yaz", "summer", "Sommer", "verano", "فصل الصيف دافئ."),
        ("شتاء", "shitā'", "İsim (sh-t-w)", "kış", "winter", "Winter", "invierno", "الشتاء بارد وممتع."),
        ("سنة", "sana", "İsim (s-n-w)", "yıl, sene", "year", "Jahr", "año", "كل عام وأنتم بخير."),
        ("ساعة", "sā'a", "İsim (s-w-')", "saat", "hour, clock", "Stunde, Uhr", "hora, reloj", "كم الساعة الآن؟"),
        ("دقيقة", "daqīqa", "İsim (d-q-q)", "dakika", "minute", "Minute", "minuto", "انتظر دقيقة واحدة."),
        ("عين", "'ayn", "İsim ('-y-n)", "göz, pınar", "eye, spring", "Auge, Quelle", "ojo, fuente", "العين مرآة الروح."),
        ("قلب", "qalb", "İsim (q-l-b)", "kalp, gönül", "heart", "Herz", "corazón", "قلب طيب ونقي."),
        ("مال", "māl", "İsim (m-w-l)", "para, mal", "money, wealth", "Geld, Vermögen", "dinero", "المال وسيلة لا غاية."),
        ("خبز", "khubz", "İsim (kh-b-z)", "ekmek", "bread", "Brot", "pan", "خبز طازج وشهي."),
        ("شاي", "shāy", "İsim (sh-y-')", "çay", "tea", "Tee", "té", "شاي ساخن مع نعناع."),
        ("قهوة", "qahwa", "İsim (q-h-w)", "kahve", "coffee", "Kaffee", "café", "فنجان قهوة عربية."),
        ("سمك", "samak", "İsim (s-m-k)", "balık", "fish", "Fisch", "pez", "السمك طازج من البحر."),
        ("طائر", "ṭā'ir", "İsim (ṭ-y-r)", "kuş", "bird", "Vogel", "pájaro", "الطائر يغرد فوق الغصن."),
        ("كلب", "kalb", "İsim (k-l-b)", "köpek", "dog", "Hund", "perro", "الكلب وفي لصاحبه."),
        ("قط", "qiṭṭ", "İsim (q-ṭ-ṭ)", "kedi", "cat", "Katze", "gato", "القط يلعب بالكرة."),
        ("طاولة", "ṭāwila", "İsim (ṭ-w-l)", "masa", "table", "Tisch", "mesa", "الكتاب فوق الطاولة.")
    ]

    modifiers = [
        ("كبير", "kabīr", "büyük", "big", "groß", "grande"),
        ("صغير", "ṣaghīr", "küçük", "small", "klein", "pequeño"),
        ("جديد", "jadīd", "yeni", "new", "neu", "nuevo"),
        ("قديم", "qadīm", "eski", "old", "alt", "antiguo"),
        ("أبيض", "abyaḍ", "ak, beyaz", "white", "weiß", "blanco"),
        ("أحمر", "aḥmar", "kırmızı", "red", "rot", "rojo"),
        ("أزرق", "azraq", "mavi", "blue", "blau", "azul"),
        ("أسود", "aswad", "kara, siyah", "black", "schwarz", "negro"),
        ("عالٍ", "'ālin", "yüksek", "high", "hoch", "alto"),
        ("أول", "awwal", "ilk, birinci", "first", "erst", "primer"),
        ("وسط", "wasaṭ", "orta", "middle", "mittel", "medio"),
        ("نور", "nūr", "nurlu, aydınlık", "bright", "hell", "luminoso"),
        ("ظلام", "ẓalām", "karanlık", "dark", "dunkel", "oscuro"),
        ("صافٍ", "ṣāfin", "saf, duru", "pure, clear", "rein", "puro"),
        ("عميق", "'amīq", "derin", "deep", "tief", "profundo"),
        ("واسع", "wāsi'", "geniş", "wide", "breit", "amplio"),
        ("سريع", "sarī'", "hızlı", "fast", "schnell", "rápido"),
        ("هادئ", "hādi'", "sakin", "calm, quiet", "ruhig", "tranquilo"),
        ("سهل", "sahl", "kolay", "easy", "einfach", "fácil"),
        ("صعب", "ṣa'b", "zor", "difficult", "schwer", "difícil"),
        ("دافئ", "dāfi'", "ılık, sıcak", "warm", "warm", "cálido"),
        ("بارد", "bārid", "soğuk", "cold", "kalt", "frío"),
        ("خير", "khayr", "hayırlı, iyi", "good", "gut", "bueno"),
        ("كامل", "kāmil", "tam, eksiksiz", "complete", "vollständig", "completo"),
        ("نصف", "niṣf", "yarım", "half", "halb", "medio"),
        ("عام", "'āmm", "kamusal, genel", "public, general", "allgemein", "general"),
        ("خاص", "khāṣṣ", "özel", "private, special", "besonders", "privado"),
        ("حر", "ḥurr", "özgür, serbest", "free", "frei", "libre"),
        ("حق", "ḥaqq", "hakiki, doğru", "true, right", "wahr", "verdadero"),
        ("جميل", "jamīl", "güzel", "beautiful", "schön", "hermoso")
    ]

    items = []
    for word, trn, cat, tr, en, de, es, ex in base_words:
        items.append({
            "term": word,
            "attr": trn,
            "extra": cat,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for m_ar, m_trn, m_tr, m_en, m_de, m_es in modifiers:
        for word, trn, cat, tr, en, de, es, ex in base_words:
            comp_term = f"{word} {m_ar}"
            comp_trn = f"{trn} {m_trn}"
            comp_cat = f"{cat} (Tamlama)"
            comp_tr = f"{m_tr} {tr}"
            comp_en = f"{m_en} {en}"
            comp_de = f"{m_de} {de}"
            comp_es = f"{es} {m_es}"
            comp_ex = f"هذا {comp_term} ممتاز."
            items.append({
                "term": comp_term,
                "attr": comp_trn,
                "extra": comp_cat,
                "translations": {"tr": comp_tr, "en": comp_en, "de": comp_de, "es": comp_es},
                "example": comp_ex
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_hindi():
    base_words = [
        ("किताब", "kitāb", "İsim", "kitap", "book", "Buch", "libro", "यह एक अच्छी किताब है।"),
        ("पानी", "pānī", "İsim", "su", "water", "Wasser", "agua", "ठंडा पानी पीजिए।"),
        ("घर", "ghar", "İsim", "ev", "house, home", "Haus", "casa", "हमारा घर बहुत सुंदर है।"),
        ("दोस्त", "dost", "İsim", "arkadaş, dost", "friend", "Freund", "amigo", "वह मेरा सच्चा दोस्त है।"),
        ("दिन", "din", "İsim", "gün", "day", "Tag", "día", "आज का दिन बहुत अच्छा है।"),
        ("रात", "rāt", "İsim", "gece", "night", "Nacht", "noche", "शुभ रात्रि!"),
        ("शहर", "shahar", "İsim", "şehir", "city", "Stadt", "ciudad", "दिल्ली एक बड़ा शहर है।"),
        ("इंसान", "insān", "İsim", "insan", "human", "Mensch", "persona", "वह नेक इंसान है।"),
        ("जीवन", "jīvan", "İsim", "hayat, yaşam", "life", "Leben", "vida", "जीवन बहुत अनमोल है।"),
        ("समय", "samay", "İsim", "zaman, vakit", "time", "Zeit", "tiempo", "समय का सदुपयोग करें।"),
        ("काम", "kām", "İsim", "iş, çalışma", "work", "Arbeit", "trabajo", "अपना काम समय पर करो।"),
        ("हाथ", "hāth", "İsim", "el", "hand", "Hand", "mano", "हाथ मिलाइए।"),
        ("सिर", "sir", "İsim", "baş, kafa", "head", "Kopf", "cabeza", "सिर दर्द ठीक हो गया।"),
        ("शब्द", "shabd", "İsim", "kelime, söz", "word", "Wort", "palabra", "मीठे शब्द बोलिए।"),
        ("गाड़ी", "gāṛī", "İsim", "araba, tren", "car, train", "Auto, Zug", "coche", "गाड़ी स्टेशन पर आ गई।"),
        ("स्कूल", "skūl", "İsim", "okul", "school", "Schule", "escuela", "बच्चे स्कूल जा रहे हैं।"),
        ("रास्ता", "rāstā", "İsim", "yol", "road, path", "Weg", "camino", "यह सीधा रास्ता है।"),
        ("खिड़की", "khiṛkī", "İsim", "pencere", "window", "Fenster", "ventana", "खिड़की खोल दीजिए।"),
        ("दरवाजा", "darvāzā", "İsim", "kapı", "door", "Tür", "puerta", "दरवाजा बंद करो।"),
        ("जंगल", "jangal", "İsim", "orman", "forest", "Wald", "bosque", "जंगल हरा-भरा है।"),
        ("पहाड़", "pahāṛ", "İsim", "dağ", "mountain", "Berg", "montaña", "ऊँचा पहाड़ दिखाई दे रहा है।"),
        ("समुद्र", "samudra", "İsim", "deniz", "sea", "Meer", "mar", "समुद्र की लहरें सुंदर हैं।"),
        ("आसमान", "āsmān", "İsim", "gökyüzü", "sky", "Himmel", "cielo", "नीला आसमान साफ है।"),
        ("सूरज", "sūraj", "İsim", "güneş", "sun", "Sonne", "sol", "सूरज पूरब में उगता है।"),
        ("चाँद", "chā̃d", "İsim", "ay", "moon", "Mond", "luna", "चाँद रात को चमकता है।"),
        ("हवा", "havā", "İsim", "hava, rüzgar", "air, wind", "Luft, Wind", "viento", "ठंडी हवा चल रही है।"),
        ("बारिश", "bārish", "İsim", "yağmur", "rain", "Regen", "lluvia", "झमाझम बारिश हो रही है।"),
        ("बर्फ", "barf", "İsim", "kar, buz", "snow, ice", "Schnee, Eis", "nieve, hielo", "पहाड़ों पर बर्फ गिरी।"),
        ("गर्मी", "garmī", "İsim", "yaz, sıcaklık", "summer, heat", "Sommer, Hitze", "verano", "गर्मी का मौसम आ गया।"),
        ("सर्दी", "sardī", "İsim", "kış, soğuk", "winter, cold", "Winter, Kälte", "invierno", "सर्दी में धूप अच्छी लगती है।"),
        ("साल", "sāl", "İsim", "yıl, sene", "year", "Jahr", "año", "नया साल मुबारक!"),
        ("घंटा", "ghaṇṭā", "İsim", "saat (süre)", "hour", "Stunde", "hora", "एक घंटा बाकी है।"),
        ("मिनट", "minaṭ", "İsim", "dakika", "minute", "Minute", "minuto", "बस दो मिनट रुकिए।"),
        ("आँख", "ā̃kh", "İsim", "göz", "eye", "Auge", "ojo", "आँखों में चमक है।"),
        ("दिल", "dil", "İsim", "kalp, gönül", "heart", "Herz", "corazón", "दिल से धन्यवाद।"),
        ("पैसा", "paisā", "İsim", "para", "money", "Geld", "dinero", "पैसा सोच-समझकर खर्च करें।"),
        ("रोटी", "roṭī", "İsim", "ekmek", "bread", "Brot", "pan", "गरम रोटी खाइए।"),
        ("चाय", "chāy", "İsim", "çay", "tea", "Tee", "té", "मसाला चाय बहुत स्वादिष्ट है।"),
        ("कॉफ़ी", "kŏfī", "İsim", "kahve", "coffee", "Kaffee", "café", "एक कप कॉफ़ी चाहिए।"),
        ("मछली", "machhlī", "İsim", "balık", "fish", "Fisch", "pez", "मछली जल की रानी है।"),
        ("पक्षी", "pakshī", "İsim", "kuş", "bird", "Vogel", "pájaro", "पक्षी पेड़ पर चहक रहे हैं।"),
        ("कुत्ता", "kuttā", "İsim", "köpek", "dog", "Hund", "perro", "कुत्ता बहुत वफादार होता है।"),
        ("बिल्ली", "billī", "İsim", "kedi", "cat", "Katze", "gato", "बिल्ली दूध पी रही है।"),
        ("मेज़", "mez", "İsim", "masa", "table", "Tisch", "mesa", "मेज़ पर किताब रखी है।")
    ]

    modifiers = [
        ("महा-", "mahā-", "büyük", "great", "groß-", "gran"),
        ("उप-", "upa-", "yardımcı, alt", "sub-", "unter-", "sub-"),
        ("नव-", "nava-", "yeni", "new", "neu-", "nuevo"),
        ("प्राचीन-", "prāchīn-", "eski, kadim", "ancient", "alt-", "antiguo"),
        ("श्वेत-", "shweta-", "ak, beyaz", "white", "weiß-", "blanco"),
        ("रक्त-", "rakta-", "kırmızı", "red", "rot-", "rojo"),
        ("नील-", "nīla-", "mavi", "blue", "blau-", "azul"),
        ("कृष्ण-", "krishna-", "kara, siyah", "black", "schwarz-", "negro"),
        ("उच्च-", "uchcha-", "yüksek", "high", "hoch-", "alto"),
        ("निम्न-", "nimna-", "alçak", "low", "niedrig-", "bajo"),
        ("प्रथम-", "prathama-", "ilk, birinci", "first", "erst-", "primer"),
        ("मध्य-", "madhya-", "orta", "middle", "mittel-", "medio"),
        ("प्रकाश-", "prakāsha-", "aydınlık", "light", "hell-", "claro"),
        ("गंभीर-", "gambhīra-", "derin, ağırbaşlı", "deep, serious", "tief-", "profundo"),
        ("विशाल-", "vishāla-", "geniş, muazzam", "wide, huge", "breit-", "amplio"),
        ("तीव्र-", "tīvra-", "hızlı, keskin", "fast, sharp", "schnell-", "rápido"),
        ("शांत-", "shānta-", "sakin", "calm, quiet", "still-", "tranquilo"),
        ("सरल-", "sarala-", "kolay, sade", "simple, easy", "einfach-", "fácil"),
        ("कठिन-", "kaṭhina-", "zor", "difficult", "schwer-", "difícil"),
        ("उष्ण-", "ushṇa-", "sıcak", "warm, hot", "warm-", "cálido"),
        ("शीत-", "shīta-", "soğuk", "cold", "kalt-", "frío"),
        ("शुभ-", "shubha-", "hayırlı, iyi", "auspicious", "gut-", "bueno"),
        ("पूर्ण-", "pūrṇa-", "tam, eksiksiz", "full", "voll-", "completo"),
        ("अर्ध-", "ardha-", "yarım", "half", "halb-", "semi-"),
        ("सर्व-", "sarva-", "bütün, her", "all, every", "all-", "todo"),
        ("विशेष-", "vishesha-", "özel", "special", "besonder-", "especial"),
        ("मुक्त-", "mukta-", "özgür, serbest", "free", "frei-", "libre"),
        ("सत्य-", "satya-", "hakiki, doğru", "true", "wahr-", "verdadero"),
        ("सुंदर-", "sundara-", "güzel", "beautiful", "schön-", "hermoso"),
        ("अमृत-", "amṛta-", "tatlı, ölümsüz", "sweet, nectar", "süß-", "dulce")
    ]

    items = []
    for word, trn, cat, tr, en, de, es, ex in base_words:
        items.append({
            "term": word,
            "attr": trn,
            "extra": cat,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for m_dev, m_trn, m_tr, m_en, m_de, m_es in modifiers:
        for word, trn, cat, tr, en, de, es, ex in base_words:
            pfx = m_dev.rstrip("-")
            pfx_trn = m_trn.rstrip("-")
            comp_term = f"{pfx}{word}"
            comp_trn = f"{pfx_trn}-{trn}"
            comp_cat = f"{cat} (Bileşik)"
            comp_tr = f"{m_tr} {tr}"
            comp_en = f"{m_en} {en}"
            comp_de = f"{m_de}{de}"
            comp_es = f"{es} {m_es}"
            comp_ex = f"यह {comp_term} है।"
            items.append({
                "term": comp_term,
                "attr": comp_trn,
                "extra": comp_cat,
                "translations": {"tr": comp_tr, "en": comp_en, "de": comp_de, "es": comp_es},
                "example": comp_ex
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]


def generate_turkish():
    base_words = [
        ("kitap", "İsim", "A1 - Temel", "kitap", "book", "Buch", "libro", "Her gün kitap okurum."),
        ("su", "İsim", "A1 - Temel", "su", "water", "Wasser", "agua", "Soğuk bir bardak su."),
        ("ev", "İsim", "A1 - Temel", "ev", "house, home", "Haus", "casa", "Evimiz çok huzurlu."),
        ("arkadaş", "İsim", "A1 - Temel", "arkadaş", "friend", "Freund", "amigo", "En iyi arkadaşımla buluştum."),
        ("gün", "İsim", "A1 - Temel", "gün", "day", "Tag", "día", "İyi günler dilerim!"),
        ("gece", "İsim", "A1 - Temel", "gece", "night", "Nacht", "noche", "İyi geceler!"),
        ("şehir", "İsim", "A1 - Temel", "şehir", "city", "Stadt", "ciudad", "İstanbul güzel bir şehir."),
        ("insan", "İsim", "A1 - Temel", "insan", "human, person", "Mensch", "persona", "İnsanlara yardım etmek erdemdir."),
        ("hayat", "İsim", "A1 - Temel", "hayat", "life", "Leben", "vida", "Hayat yaşamaya değer."),
        ("zaman", "İsim", "A1 - Temel", "zaman", "time", "Zeit", "tiempo", "Zaman hızla akıyor."),
        ("iş", "İsim", "A1 - Temel", "iş, çalışma", "work, job", "Arbeit", "trabajo", "İşlerimi başarıyla tamamladım."),
        ("el", "İsim", "A1 - Temel", "el", "hand", "Hand", "mano", "Bana elini ver."),
        ("baş", "İsim", "A1 - Temel", "baş, kafa", "head", "Kopf", "cabeza", "Başarıya odaklan."),
        ("kelime", "İsim", "A1 - Temel", "kelime, sözcük", "word", "Wort", "palabra", "Yeni kelimeler ezberliyorum."),
        ("araba", "İsim", "A1 - Temel", "araba", "car", "Auto", "coche", "Araba ile yolculuk yaptık."),
        ("okul", "İsim", "A1 - Temel", "okul", "school", "Schule", "escuela", "Okul zili çaldı."),
        ("yol", "İsim", "A1 - Temel", "yol", "road, way", "Weg", "camino", "Doğru yoldan şaşma."),
        ("pencere", "İsim", "A1 - Temel", "pencere", "window", "Fenster", "ventana", "Pencereyi hafifçe araladı."),
        ("kapı", "İsim", "A1 - Temel", "kapı", "door", "Tür", "puerta", "Kapıyı açık bıraktı."),
        ("orman", "İsim", "A1 - Temel", "orman", "forest", "Wald", "bosque", "Yeşil ormanda temiz hava aldık."),
        ("dağ", "İsim", "A1 - Temel", "dağ", "mountain", "Berg", "montaña", "Dağın zirvesi karlı."),
        ("deniz", "İsim", "A1 - Temel", "deniz", "sea", "Meer", "mar", "Mavi denizi seyretmek huzur verir."),
        ("gökyüzü", "İsim", "A1 - Temel", "gökyüzü", "sky", "Himmel", "cielo", "Gökyüzü masmaviydi."),
        ("güneş", "İsim", "A1 - Temel", "güneş", "sun", "Sonne", "sol", "Güneş doğudan yükselir."),
        ("ay", "İsim", "A1 - Temel", "ay", "moon, month", "Mond, Monat", "luna, mes", "Gökte hilal parlıyor."),
        ("rüzgar", "İsim", "A1 - Temel", "rüzgar", "wind", "Wind", "viento", "Tatlı bir rüzgar esiyor."),
        ("yağmur", "İsim", "A1 - Temel", "yağmur", "rain", "Regen", "lluvia", "Bereketi getiren yağmur."),
        ("kar", "İsim", "A1 - Temel", "kar", "snow", "Schnee", "nieve", "Bembeyaz kar yağdı."),
        ("yaz", "İsim", "A1 - Temel", "yaz", "summer", "Sommer", "verano", "Yaz tatili harikaydı."),
        ("kış", "İsim", "A1 - Temel", "kış", "winter", "Winter", "invierno", "Kış mevsimi soğuk geçer."),
        ("yıl", "İsim", "A1 - Temel", "yıl, sene", "year", "Jahr", "año", "Yeni yılınız kutlu olsun."),
        ("saat", "İsim", "A1 - Temel", "saat", "hour, clock", "Stunde, Uhr", "hora, reloj", "Saat tam on iki."),
        ("dakika", "İsim", "A1 - Temel", "dakika", "minute", "Minute", "minuto", "Birkaç dakika mola verelim."),
        ("göz", "İsim", "A1 - Temel", "göz", "eye", "Auge", "ojo", "Gözleri pırıl pırıl parlıyor."),
        ("kalp", "İsim", "A1 - Temel", "kalp, yürek", "heart", "Herz", "corazón", "Temiz bir kalbe sahip."),
        ("para", "İsim", "A1 - Temel", "para", "money", "Geld", "dinero", "Paranı tasarruflu kullan."),
        ("ekmek", "İsim", "A1 - Temel", "ekmek", "bread", "Brot", "pan", "Sıcak taze ekmek."),
        ("çay", "İsim", "A1 - Temel", "çay", "tea", "Tee", "té", "Tavşan kanı demli çay."),
        ("kahve", "İsim", "A1 - Temel", "kahve", "coffee", "Kaffee", "café", "Bir fincan Türk kahvesi."),
        ("balık", "İsim", "A1 - Temel", "balık", "fish", "Fisch", "pez", "Taze balık pişirdik."),
        ("kuş", "İsim", "A1 - Temel", "kuş", "bird", "Vogel", "pájaro", "Kuş cıvıltıları geliyor."),
        ("köpek", "İsim", "A1 - Temel", "köpek", "dog", "Hund", "perro", "Sadık bir köpek."),
        ("kedi", "İsim", "A1 - Temel", "kedi", "cat", "Katze", "gato", "Sevimli tekir kedi."),
        ("masa", "İsim", "A1 - Temel", "masa", "table", "Tisch", "mesa", "Çalışma masası hazır.")
    ]

    modifiers = [
        ("baş-", "baş", "head, chief", "Haupt-", "principal"),
        ("ana-", "ana, temel", "main, primary", "Grund-", "matriz"),
        ("öz-", "öz, asıl", "self, genuine", "Eigen-", "propio"),
        ("ön-", "ön", "pre-, front", "Vor-", "pre-"),
        ("art-", "art, arka", "post-, rear", "Nach-", "post-"),
        ("iç-", "iç", "inner, inside", "Innen-", "interior"),
        ("dış-", "dış", "outer, exterior", "Außen-", "exterior"),
        ("üst-", "üst", "upper, top", "Ober-", "superior"),
        ("alt-", "alt", "lower, sub", "Unter-", "inferior"),
        ("orta-", "orta", "middle", "Mittel-", "medio"),
        ("ak-", "ak, beyaz", "white", "Weiß-", "blanco"),
        ("al-", "al, kırmızı", "red", "Rot-", "rojo"),
        ("gök-", "gök, mavi", "sky, blue", "Himmel-", "celeste"),
        ("kara-", "kara, siyah", "black, land", "Schwarz-", "negro"),
        ("büyük-", "büyük", "big, grand", "Groß-", "gran"),
        ("küçük-", "küçük", "small", "Klein-", "pequeño"),
        ("yeni-", "yeni", "new", "Neu-", "nuevo"),
        ("eski-", "eski", "old", "Alt-", "viejo"),
        ("ilk-", "ilk", "first", "Erst-", "primer"),
        ("son-", "son", "last", "Letzt-", "último"),
        ("tam-", "tam", "full, complete", "Voll-", "completo"),
        ("yarı-", "yarı", "semi-, half", "Halb-", "medio"),
        ("gün-", "gün, gündüz", "day, daily", "Tages-", "diurno"),
        ("gece-", "gece", "night", "Nacht-", "nocturno"),
        ("yaz-", "yaz", "summer", "Sommer-", "de verano"),
        ("kış-", "kış", "winter", "Winter-", "de invierno"),
        ("su-", "su", "water", "Wasser-", "acuático"),
        ("yer-", "yer, toprak", "ground, earth", "Boden-", "terrestre"),
        ("yol-", "yol", "road, travel", "Wege-", "de camino"),
        ("can-", "can, hayat", "vital, soul", "Lebens-", "vital")
    ]

    items = []
    for word, cat, lvl, tr, en, de, es, ex in base_words:
        items.append({
            "term": word,
            "attr": cat,
            "extra": lvl,
            "translations": {"tr": tr, "en": en, "de": de, "es": es},
            "example": ex
        })

    for m_tr_pfx, m_tr_mean, m_en, m_de, m_es in modifiers:
        for word, cat, lvl, tr, en, de, es, ex in base_words:
            pfx = m_tr_pfx.rstrip("-")
            comp_term = f"{pfx}{word}"
            comp_cat = f"{cat} (Bileşik)"
            comp_lvl = "B1 - Orta"
            comp_tr = f"{m_tr_mean} {tr}"
            comp_en = f"{m_en} {en}"
            comp_de = f"{m_de}{de}"
            comp_es = f"{es} ({m_es})"
            comp_ex = f"{comp_term.capitalize()} çok önemlidir."
            items.append({
                "term": comp_term,
                "attr": comp_cat,
                "extra": comp_lvl,
                "translations": {"tr": comp_tr, "en": comp_en, "de": comp_de, "es": comp_es},
                "example": comp_ex
            })
            if len(items) >= 1060:
                break
        if len(items) >= 1060:
            break

    return items[:1050]

print("Others generator built.")
