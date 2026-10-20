"""
Study Card - Evrensel Diller Kataloğu (Universal Languages Registry)
Dünyadaki tüm yaygın ve bölgesel dilleri, ISO kodlarını, çok dilli karşılıklarını (TR, EN, DE, ES),
telaffuz ve sözlük anahtarlarını barındırır.
Kullanıcı arayüz diline göre (İngilizce ise "French", Türkçe ise "Fransızca") aratıp seçebilir.
"""

from typing import List, Dict, Optional, Any
import unicodedata

# 76 Kapsamlı Dünya Dilleri Listesi - Çok Dilli (TR, EN, DE, ES)
LANGUAGES_DATA: List[Dict[str, Any]] = [
    {"code": "en", "tr": "İngilizce", "en": "English", "de": "Englisch", "es": "Inglés", "cambridge": "english"},
    {"code": "tr", "tr": "Türkçe", "en": "Turkish", "de": "Türkisch", "es": "Turco", "cambridge": "turkish"},
    {"code": "de", "tr": "Almanca", "en": "German", "de": "Deutsch", "es": "Alemán", "cambridge": "german"},
    {"code": "fr", "tr": "Fransızca", "en": "French", "de": "Französisch", "es": "Francés", "cambridge": "french"},
    {"code": "es", "tr": "İspanyolca", "en": "Spanish", "de": "Spanisch", "es": "Español", "cambridge": "spanish"},
    {"code": "it", "tr": "İtalyanca", "en": "Italian", "de": "Italienisch", "es": "Italiano", "cambridge": "italian"},
    {"code": "ru", "tr": "Rusça", "en": "Russian", "de": "Russisch", "es": "Ruso", "cambridge": "russian"},
    {"code": "ar", "tr": "Arapça", "en": "Arabic", "de": "Arabisch", "es": "Árabe", "cambridge": "arabic"},
    {"code": "ja", "tr": "Japonca", "en": "Japanese", "de": "Japanisch", "es": "Japonés", "cambridge": "japanese"},
    {"code": "ko", "tr": "Korece", "en": "Korean", "de": "Koreanisch", "es": "Coreano", "cambridge": "korean"},
    {"code": "zh", "tr": "Çince (Basitleştirilmiş)", "en": "Chinese (Simplified)", "de": "Chinesisch (Vereinfacht)", "es": "Chino (Simplificado)", "cambridge": "chinese-simplified"},
    {"code": "zh-tw", "tr": "Çince (Geleneksel)", "en": "Chinese (Traditional)", "de": "Chinesisch (Traditionell)", "es": "Chino (Tradicional)", "cambridge": "chinese-traditional"},
    {"code": "pt", "tr": "Portekizce", "en": "Portuguese", "de": "Portugiesisch", "es": "Portugués", "cambridge": "portuguese"},
    {"code": "nl", "tr": "Felemenkçe (Hollandaca)", "en": "Dutch", "de": "Niederländisch", "es": "Holandés", "cambridge": "dutch"},
    {"code": "pl", "tr": "Lehçe (Polonyaca)", "en": "Polish", "de": "Polnisch", "es": "Polaco", "cambridge": "polish"},
    {"code": "el", "tr": "Yunanca", "en": "Greek", "de": "Griechisch", "es": "Griego", "cambridge": "greek"},
    {"code": "sv", "tr": "İsveççe", "en": "Swedish", "de": "Schwedisch", "es": "Sueco", "cambridge": "swedish"},
    {"code": "no", "tr": "Norveççe", "en": "Norwegian", "de": "Norwegisch", "es": "Noruego", "cambridge": "norwegian"},
    {"code": "da", "tr": "Danca", "en": "Danish", "de": "Dänisch", "es": "Danés", "cambridge": "danish"},
    {"code": "fi", "tr": "Fince", "en": "Finnish", "de": "Finnisch", "es": "Finlandés", "cambridge": "finnish"},
    {"code": "cs", "tr": "Çekçe", "en": "Czech", "de": "Tschechisch", "es": "Checo", "cambridge": "czech"},
    {"code": "hu", "tr": "Macarca", "en": "Hungarian", "de": "Ungarisch", "es": "Húngaro", "cambridge": "hungarian"},
    {"code": "ro", "tr": "Romence", "en": "Romanian", "de": "Rumänisch", "es": "Rumano", "cambridge": "romanian"},
    {"code": "bg", "tr": "Bulgarca", "en": "Bulgarian", "de": "Bulgarisch", "es": "Búlgaro", "cambridge": "bulgarian"},
    {"code": "uk", "tr": "Ukraynaca", "en": "Ukrainian", "de": "Ukrainisch", "es": "Ucraniano", "cambridge": "ukrainian"},
    {"code": "hr", "tr": "Hırvatça", "en": "Croatian", "de": "Kroatisch", "es": "Croata", "cambridge": "croatian"},
    {"code": "sr", "tr": "Sırpça", "en": "Serbian", "de": "Serbisch", "es": "Serbio", "cambridge": "serbian"},
    {"code": "sk", "tr": "Slovakça", "en": "Slovak", "de": "Slowakisch", "es": "Eslovaco", "cambridge": "slovak"},
    {"code": "sl", "tr": "Slovence", "en": "Slovenian", "de": "Slowenisch", "es": "Esloveno", "cambridge": "slovenian"},
    {"code": "id", "tr": "Endonezce", "en": "Indonesian", "de": "Indonesisch", "es": "Indonesio", "cambridge": "indonesian"},
    {"code": "ms", "tr": "Malayca", "en": "Malay", "de": "Malaiisch", "es": "Malayo", "cambridge": "malaysian"},
    {"code": "vi", "tr": "Vietnamca", "en": "Vietnamese", "de": "Vietnamesisch", "es": "Vietnamita", "cambridge": "vietnamese"},
    {"code": "th", "tr": "Tayca", "en": "Thai", "de": "Thailändisch", "es": "Tailandés", "cambridge": "thai"},
    {"code": "tl", "tr": "Filipince (Tagalog)", "en": "Filipino (Tagalog)", "de": "Filipino (Tagalog)", "es": "Filipino (Tagalo)", "cambridge": "tagalog"},
    {"code": "hi", "tr": "Hintçe", "en": "Hindi", "de": "Hindi", "es": "Hindi", "cambridge": "hindi"},
    {"code": "fa", "tr": "Farsça", "en": "Persian", "de": "Persisch", "es": "Persa", "cambridge": "persian"},
    {"code": "he", "tr": "İbranice", "en": "Hebrew", "de": "Hebräisch", "es": "Hebreo", "cambridge": "hebrew"},
    {"code": "bn", "tr": "Bengalce", "en": "Bengali", "de": "Bengalisch", "es": "Bengalí", "cambridge": "bengali"},
    {"code": "ur", "tr": "Urduca", "en": "Urdu", "de": "Urdu", "es": "Urdu", "cambridge": "urdu"},
    {"code": "az", "tr": "Azerice", "en": "Azerbaijani", "de": "Aserbaidschanisch", "es": "Azerbaiyano", "cambridge": "azerbaijani"},
    {"code": "kk", "tr": "Kazakça", "en": "Kazakh", "de": "Kasachisch", "es": "Kazajo", "cambridge": "kazakh"},
    {"code": "uz", "tr": "Özbekçe", "en": "Uzbek", "de": "Usbekisch", "es": "Uzbeko", "cambridge": "uzbek"},
    {"code": "ky", "tr": "Kırgızca", "en": "Kyrgyz", "de": "Kirgisisch", "es": "Kirguís", "cambridge": "kyrgyz"},
    {"code": "tk", "tr": "Türkmence", "en": "Turkmen", "de": "Turkmenisch", "es": "Turcomano", "cambridge": "turkmen"},
    {"code": "tt", "tr": "Tatarca", "en": "Tatar", "de": "Tatarisch", "es": "Tártaro", "cambridge": "tatar"},
    {"code": "ca", "tr": "Katalanca", "en": "Catalan", "de": "Katalanisch", "es": "Catalán", "cambridge": "catalan"},
    {"code": "eu", "tr": "Baskça", "en": "Basque", "de": "Baskisch", "es": "Vasco", "cambridge": "basque"},
    {"code": "gl", "tr": "Galiçyaca", "en": "Galician", "de": "Galizisch", "es": "Gallego", "cambridge": "galician"},
    {"code": "ga", "tr": "İrlandaca", "en": "Irish", "de": "Irisch", "es": "Irlandés", "cambridge": "irish"},
    {"code": "cy", "tr": "Galce", "en": "Welsh", "de": "Walisisch", "es": "Galés", "cambridge": "welsh"},
    {"code": "is", "tr": "İzlandaca", "en": "Icelandic", "de": "Isländisch", "es": "Islandés", "cambridge": "icelandic"},
    {"code": "lt", "tr": "Litvanca", "en": "Lithuanian", "de": "Litauisch", "es": "Lituano", "cambridge": "lithuanian"},
    {"code": "lv", "tr": "Letonca", "en": "Latvian", "de": "Lettisch", "es": "Letón", "cambridge": "latvian"},
    {"code": "et", "tr": "Estonca", "en": "Estonian", "de": "Estnisch", "es": "Estonio", "cambridge": "estonian"},
    {"code": "ka", "tr": "Gürcüce", "en": "Georgian", "de": "Georgisch", "es": "Georgiano", "cambridge": "georgian"},
    {"code": "hy", "tr": "Ermenice", "en": "Armenian", "de": "Armenisch", "es": "Armenio", "cambridge": "armenian"},
    {"code": "mn", "tr": "Moğolca", "en": "Mongolian", "de": "Mongolisch", "es": "Mongol", "cambridge": "mongolian"},
    {"code": "sq", "tr": "Arnavutça", "en": "Albanian", "de": "Albanisch", "es": "Albanés", "cambridge": "albanian"},
    {"code": "mk", "tr": "Makedonca", "en": "Macedonian", "de": "Mazedonisch", "es": "Macedonio", "cambridge": "macedonian"},
    {"code": "bs", "tr": "Boşnakça", "en": "Bosnian", "de": "Bosnisch", "es": "Bosnio", "cambridge": "bosnian"},
    {"code": "sw", "tr": "Svahili", "en": "Swahili", "de": "Swahili", "es": "Suajili", "cambridge": "swahili"},
    {"code": "af", "tr": "Afrikaans", "en": "Afrikaans", "de": "Afrikaans", "es": "Afrikáans", "cambridge": "afrikaans"},
    {"code": "la", "tr": "Latince", "en": "Latin", "de": "Latein", "es": "Latín", "cambridge": "latin"},
    {"code": "eo", "tr": "Esperanto", "en": "Esperanto", "de": "Esperanto", "es": "Esperanto", "cambridge": "esperanto"},
    {"code": "ta", "tr": "Tamilce", "en": "Tamil", "de": "Tamil", "es": "Tamil", "cambridge": "tamil"},
    {"code": "te", "tr": "Teluguca", "en": "Telugu", "de": "Telugu", "es": "Telugu", "cambridge": "telugu"},
    {"code": "mr", "tr": "Marathice", "en": "Marathi", "de": "Marathi", "es": "Maratí", "cambridge": "marathi"},
    {"code": "ml", "tr": "Malayalamca", "en": "Malayalam", "de": "Malayalam", "es": "Malayalam", "cambridge": "malayalam"},
    {"code": "kn", "tr": "Kannada", "en": "Kannada", "de": "Kannada", "es": "Canarés", "cambridge": "kannada"},
    {"code": "si", "tr": "Seylanca", "en": "Sinhala", "de": "Singhalesisch", "es": "Cingalés", "cambridge": "sinhala"},
    {"code": "my", "tr": "Burmaca (Myanmar)", "en": "Burmese", "de": "Birmanisch", "es": "Birmano", "cambridge": "burmese"},
    {"code": "km", "tr": "Kmerce (Kamboçyaca)", "en": "Khmer", "de": "Khmer", "es": "Jemer", "cambridge": "khmer"},
    {"code": "lo", "tr": "Laoca", "en": "Lao", "de": "Laotisch", "es": "Lao", "cambridge": "lao"},
    {"code": "am", "tr": "Amharca", "en": "Amharic", "de": "Amharisch", "es": "Amárico", "cambridge": "amharic"},
    {"code": "so", "tr": "Somalice", "en": "Somali", "de": "Somali", "es": "Somalí", "cambridge": "somali"},
    {"code": "yi", "tr": "Yidiş", "en": "Yiddish", "de": "Jiddisch", "es": "Yidis", "cambridge": "yiddish"},
]

# Geriye dönük uyumluluk için "name" alanı
for item in LANGUAGES_DATA:
    item["name"] = item["tr"]


def normalize_string(s: str) -> str:
    """Türkçe ve uluslararası karakterleri normalleştirerek arama uyumlu hale getirir."""
    if not s:
        return ""
    s = s.replace("İ", "i").replace("I", "ı").lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def get_languages(ui_lang='tr'):
    return [(row.get(ui_lang, row['en']), row['code']) for row in LANGUAGES_DATA]


def get_all_language_names(ui_lang: str = "tr") -> List[str]:
    """Arayüz diline uygun dillerin isim listesini döner (örn: EN için 'French', TR için 'Fransızca')."""
    lang_key = ui_lang if ui_lang in ("tr", "en", "de", "es") else "en"
    return [lang.get(lang_key, lang.get("en", lang.get("tr", ""))) for lang in LANGUAGES_DATA]


def get_language_code(name_or_code: str) -> str:
    """Dil adı veya kodundan ISO dil kodunu (örn: 'en', 'de', 'fr', 'tr') bulur.
    Tüm dillerdeki (EN, TR, DE, ES) isimlerle ve ISO kodlarıyla tam ve kısmi eşleşmeyi destekler."""
    if not name_or_code:
        return "en"
    clean = normalize_string(name_or_code.strip())

    # 1. Doğrudan ISO kod eşleşmesi
    for item in LANGUAGES_DATA:
        if item["code"].lower() == clean:
            return item["code"]

    # 2. Çok dilli tam isim eşleşmesi (tr, en, de, es, name)
    for item in LANGUAGES_DATA:
        for k in ("en", "tr", "de", "es", "name"):
            val = item.get(k)
            if val and normalize_string(val) == clean:
                return item["code"]

    # 3. Kısmi eşleşme
    for item in LANGUAGES_DATA:
        for k in ("en", "tr", "de", "es", "name"):
            val = item.get(k)
            if val:
                norm_val = normalize_string(val)
                if clean in norm_val or norm_val in clean:
                    return item["code"]

    return "en"


def get_language_name(code_or_name: str, ui_lang: str = "tr") -> str:
    """Dil kodu veya adından seçilen arayüz dilindeki kullanıcı dostu dil adını döner."""
    if not code_or_name:
        code_or_name = 'en'

    code = get_language_code(code_or_name)
    lang_key = ui_lang if ui_lang in ("tr", "en", "de", "es") else "en"
    for item in LANGUAGES_DATA:
        if item["code"] == code:
            return item.get(lang_key, item.get("en", item.get("tr", code_or_name)))

    return code_or_name


def get_cambridge_slug(name_or_code: str) -> str:
    """Cambridge sözlük url slug'ını döner."""
    code = get_language_code(name_or_code)
    for item in LANGUAGES_DATA:
        if item["code"] == code:
            return item["cambridge"]
    return "turkish"


def detect_card_term_language(card: dict) -> str:
    """
    Kartın teriminin hangi yabancı dilde yazıldığını akıllıca tespit eder.
    Asla Türkçe anlam dilini (target_lang) yabancı kelimenin fonetiği olarak kullanmaz!
    """
    if not card:
        return "en"

    term = card.get("term", "").strip()
    source_lang = card.get("source_lang", "").strip()
    deck_name = card.get("deck_name", "").strip().lower()

    # 1. Script bazlı doğrudan tespit
    if any("\u0400" <= c <= "\u04ff" for c in term):
        return "ru"
    if any("\u0600" <= c <= "\u06ff" for c in term):
        return "ar"
    if any("\u4e00" <= c <= "\u9fff" for c in term):
        return "zh"
    if any("\u3040" <= c <= "\u30ff" for c in term):
        return "ja"
    if any("\uac00" <= c <= "\ud7af" for c in term):
        return "ko"
    if any("\u0900" <= c <= "\u097f" for c in term):
        return "hi"

    # 2. Deste adından dil tespiti
    if any(k in deck_name for k in ("almanca", "german", "artikel")):
        return "de"
    elif any(k in deck_name for k in ("fransızca", "french")):
        return "fr"
    elif any(k in deck_name for k in ("ispanyolca", "i̇spanyolca", "spanish")):
        return "es"
    elif any(k in deck_name for k in ("italyanca", "i̇talyanca", "italian")):
        return "it"
    elif any(k in deck_name for k in ("rusça", "russian")):
        return "ru"
    elif any(k in deck_name for k in ("arapça", "arabic")):
        return "ar"
    elif any(k in deck_name for k in ("isveççe", "i̇sveççe", "swedish")):
        return "sv"
    elif any(k in deck_name for k in ("portekizce", "portuguese")):
        return "pt"
    elif any(k in deck_name for k in ("hollandaca", "dutch", "felemenkçe")):
        return "nl"
    elif any(k in deck_name for k in ("korece", "korean")):
        return "ko"
    elif any(k in deck_name for k in ("japonca", "japanese")):
        return "ja"
    elif any(k in deck_name for k in ("hintçe", "hindi")):
        return "hi"
    elif any(k in deck_name for k in ("ingilizce", "i̇ngilizce", "english", "verb", "phrasal", "daily")):
        return "en"

    # 3. Kelimenin karakteristik özellikleri
    term_lower = term.lower().strip()
    if (term_lower.startswith(("der ", "die ", "das ")) or any(c in term_lower for c in ("ä", "ö", "ü", "ß"))
            or term_lower in ("guten tag", "danke", "bitte", "tschüss", "auf wiedersehen")):
        return "de"
    if (term_lower.startswith(("le ", "la ", "l'", "les ", "un ", "une ")) or any(c in term_lower for c in ("é", "è", "ê", "ç", "à", "ù"))
            or term_lower in ("bonjour", "merci", "salut", "au revoir", "s'il vous plaît", "oui")):
        return "fr"
    if (term_lower.startswith(("el ", "los ", "las ")) or any(c in term_lower for c in ("ñ", "¿", "¡"))
            or term_lower.startswith("hola ") or term_lower in ("hola", "gracias", "por favor", "buenos días", "buenas noches", "adiós")):
        return "es"

    # 4. source_lang kontrolü (Karttaki kaynak dil yabancı dil ise)
    if source_lang:
        c_code = get_language_code(source_lang)
        if c_code and c_code not in ("tr", "turkish", "türkçe"):
            return c_code
        elif c_code == "tr" and (any(ch in term.lower() for ch in ("ç", "ğ", "ı", "ö", "ş", "ü")) or (card.get("target_lang") and get_language_code(card.get("target_lang", "")) not in ("tr", ""))):
            return "tr"

    # 5. target_lang kontrolü (Eğer target_lang Türkçe HARİCİ bir yabancı dil ise)
    target_lang = card.get("target_lang", "").strip()
    if target_lang:
        t_code = get_language_code(target_lang)
        if t_code and t_code not in ("tr", "turkish", "türkçe"):
            return t_code

    return "en"
