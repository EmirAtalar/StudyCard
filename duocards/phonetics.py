"""
Study Card - Çok Dilli Otomatik Fonetik Telaffuz Motoru (Multilingual IPA Engine)
İngilizce (İngiliz/Amerikan), Almanca, İspanyolca, Fransızca ve Türkçe için
otomatik IPA fonetik okunuş üretir ve kullanıcının telaffuz dilini/aksanını seçmesine olanak tanır.
"""

import re
from typing import Dict, List, Tuple

AVAILABLE_ACCENTS: List[Tuple[str, str]] = [
    ("en-uk", "UK English (British)"),
    ("en-us", "US English (American)"),
    ("de", "Deutsch (German)"),
    ("es", "Español (Spanish)"),
    ("fr", "Français (French)"),
    ("tr", "Türkçe (Turkish)")
]

# Temel İngilizce İngiliz (UK) IPA Sözlüğü
_IPA_DICT_UK: Dict[str, str] = {
    "the": "/ðə/", "be": "/biː/", "to": "/tuː/", "of": "/ɒv/", "and": "/ænd/",
    "a": "/ə/", "in": "/ɪn/", "that": "/ðæt/", "have": "/hæv/", "i": "/aɪ/",
    "it": "/ɪt/", "for": "/fɔːr/", "not": "/nɒt/", "on": "/ɒn/", "with": "/wɪð/",
    "he": "/hiː/", "as": "/æz/", "you": "/juː/", "do": "/duː/", "at": "/æt/",
    "this": "/ðɪs/", "but": "/bʌt/", "his": "/hɪz/", "by": "/baɪ/", "from": "/frɒm/",
    "they": "/ðeɪ/", "we": "/wiː/", "say": "/seɪ/", "her": "/hɜːr/", "she": "/ʃiː/",
    "or": "/ɔːr/", "an": "/æn/", "will": "/wɪl/", "my": "/maɪ/", "one": "/wʌn/",
    "all": "/ɔːl/", "would": "/wʊd/", "there": "/ðeər/", "their": "/ðeər/",
    "what": "/wɒt/", "so": "/səʊ/", "up": "/ʌp/", "out": "/aʊt/", "if": "/ɪf/",
    "about": "/əˈbaʊt/", "who": "/huː/", "get": "/ɡet/", "which": "/wɪtʃ/",
    "go": "/ɡəʊ/", "me": "/miː/", "when": "/wen/", "make": "/meɪk/", "can": "/kæn/",
    "like": "/laɪk/", "time": "/taɪm/", "no": "/nəʊ/", "just": "/dʒʌst/",
    "him": "/hɪm/", "know": "/nəʊ/", "take": "/teɪk/", "people": "/ˈpiː.pəl/",
    "year": "/jɪər/", "your": "/jɔːr/", "good": "/ɡʊd/", "some": "/sʌm/",
    "could": "/kʊd/", "them": "/ðem/", "see": "/siː/", "other": "/ˈʌð.ər/",
    "apple": "/ˈæp.əl/", "water": "/ˈwɔː.tər/", "resilient": "/rɪˈzɪl.jənt/",
    "meticulous": "/məˈtɪk.jə.ləs/", "inevitable": "/ɪnˈev.ɪ.tə.bəl/",
    "candid": "/ˈkæn.dɪd/", "eloquent": "/ˈel.ə.kwənt/", "break a leg": "/breɪk ə leɡ/",
    "under the weather": "/ˈʌn.dər ðə ˈweð.ər/", "piece of cake": "/piːs əv keɪk/",
    "call it a day": "/kɔːl ɪt ə deɪ/", "run out of": "/rʌn aʊt əv/", "give up": "/ɡɪv ʌp/"
}

# 200 temel kelime havuzundaki tüm fonetikleri de sözlüğe ekle
try:
    from duocards.word_data import FULL_200_WORDS
    for item in FULL_200_WORDS:
        term = item[0].lower().strip()
        phonetic = item[5].strip()
        if term and phonetic and term not in _IPA_DICT_UK:
            _IPA_DICT_UK[term] = phonetic
except Exception:
    pass


def _to_us_ipa(uk_ipa: str) -> str:
    """UK IPA telaffuzunu Amerikan (General American) kurallarına dönüştürür."""
    res = uk_ipa
    # /ɒ/ -> /ɑː/ (örn: not /nɒt/ -> /nɑːt/, hot /hɒt/ -> /hɑːt/)
    res = res.replace("ɒ", "ɑː")
    # /ɔː/ -> /ɔːr/ veya /ɑː/
    res = res.replace("ɔː/", "ɔːr/")
    # /əʊ/ -> /oʊ/ (go /ɡəʊ/ -> /ɡoʊ/, no /nəʊ/ -> /noʊ/)
    res = res.replace("əʊ", "oʊ")
    return res


def _rule_based_english(w: str, accent: str = "en-uk") -> str:
    res = w.lower().strip()
    res = re.sub(r"tion$", "ʃən", res)
    res = re.sub(r"sion$", "ʒən", res)
    res = re.sub(r"ture$", "tʃər", res)
    res = re.sub(r"cial$", "ʃəl", res)
    res = re.sub(r"tial$", "ʃəl", res)
    res = re.sub(r"cious$", "ʃəs", res)
    res = re.sub(r"ph", "f", res)
    res = re.sub(r"sh", "ʃ", res)
    res = re.sub(r"ch", "tʃ", res)
    res = re.sub(r"th", "θ", res)
    res = re.sub(r"ck", "k", res)
    res = re.sub(r"ng", "ŋ", res)
    res = re.sub(r"ee|ea", "iː", res)
    res = re.sub(r"oo", "uː", res)
    res = re.sub(r"ou|ow", "aʊ", res)
    res = re.sub(r"ai|ay", "eɪ", res)
    res = re.sub(r"c(?=[eiy])", "s", res)
    res = re.sub(r"c", "k", res)
    res = re.sub(r"j", "dʒ", res)
    ipa = f"/ˈ{res}/"
    if accent == "en-us":
        ipa = _to_us_ipa(ipa)
    return ipa


def _rule_based_german(w: str) -> str:
    res = w.lower().strip()
    res = re.sub(r"sch", "ʃ", res)
    res = re.sub(r"ch", "ç", res)
    res = re.sub(r"ei|ey", "aɪ", res)
    res = re.sub(r"eu|äu", "ɔʏ", res)
    res = re.sub(r"ie", "iː", res)
    res = re.sub(r"sp", "ʃp", res)
    res = re.sub(r"st", "ʃt", res)
    res = re.sub(r"z", "ts", res)
    res = re.sub(r"w", "v", res)
    res = re.sub(r"v", "f", res)
    res = re.sub(r"j", "j", res)
    res = re.sub(r"ß", "s", res)
    return f"/ˈ{res}/"


def _rule_based_spanish(w: str) -> str:
    res = w.lower().strip()
    res = re.sub(r"ll", "ʎ", res)
    res = re.sub(r"rr", "r", res)
    res = re.sub(r"ñ", "ɲ", res)
    res = re.sub(r"ch", "tʃ", res)
    res = re.sub(r"j", "x", res)
    res = re.sub(r"ge|gi", "xe", res)
    res = re.sub(r"z|ce|ci", "θ", res)
    res = re.sub(r"c", "k", res)
    res = re.sub(r"v", "b", res)
    res = re.sub(r"h", "", res)
    return f"/ˈ{res}/"


def _rule_based_french(w: str) -> str:
    res = w.lower().strip()
    res = re.sub(r"ou", "u", res)
    res = re.sub(r"eau|au", "o", res)
    res = re.sub(r"oi", "wa", res)
    res = re.sub(r"ch", "ʃ", res)
    res = re.sub(r"ph", "f", res)
    res = re.sub(r"qu", "k", res)
    res = re.sub(r"[tds]$", "", res)
    return f"/{res}/"


def _rule_based_turkish(w: str) -> str:
    res = w.lower().strip()
    res = res.replace("c", "dʒ").replace("ç", "tʃ").replace("ğ", "ː").replace("ş", "ʃ")
    return f"/ˈ{res}/"


def get_phonetic(term: str, lang_accent: str = "en-uk") -> str:
    """
    Verilen kelime/deyim için seçilen dil veya aksanda (UK, US, DE, ES, FR, TR)
    otomatik IPA fonetik okunuş üretir.
    """
    clean_term = term.strip().lower()
    if not clean_term:
        return ""

    accent = lang_accent.lower().strip()

    # 1. Almanca
    if accent in ["de", "german", "deutsch"]:
        return _rule_based_german(clean_term)

    # 2. İspanyolca
    if accent in ["es", "spanish", "español"]:
        return _rule_based_spanish(clean_term)

    # 3. Fransızca
    if accent in ["fr", "french", "français"]:
        return _rule_based_french(clean_term)

    # 4. Türkçe
    if accent in ["tr", "turkish", "türkçe"]:
        return _rule_based_turkish(clean_term)

    # 5. İtalyanca
    if accent in ["it", "italian", "italyanca"]:
        res = clean_term
        res = re.sub(r"gli", "ʎi", res)
        res = re.sub(r"gn", "ɲ", res)
        res = re.sub(r"c(?=[eiy])", "tʃ", res)
        res = re.sub(r"g(?=[eiy])", "dʒ", res)
        res = re.sub(r"ch", "k", res)
        res = re.sub(r"gh", "ɡ", res)
        return f"/ˈ{res}/"

    # 6. İngilizce (UK ve US)
    if accent in ["en", "en-uk", "en-us", "english", "ingilizce"] or not accent:
        if clean_term in _IPA_DICT_UK:
            uk_ipa = _IPA_DICT_UK[clean_term]
            return _to_us_ipa(uk_ipa) if accent == "en-us" else uk_ipa

        words = clean_term.split()
        if len(words) > 1:
            parts = []
            for w in words:
                w_c = re.sub(r"[^\w]", "", w)
                if not w_c:
                    continue
                if w_c in _IPA_DICT_UK:
                    p = _IPA_DICT_UK[w_c].strip("/")
                    if accent == "en-us":
                        p = _to_us_ipa(f"/{p}/").strip("/")
                else:
                    p = _rule_based_english(w_c, accent).strip("/")
                parts.append(p)
            return "/" + " ".join(parts) + "/"

        w_c = re.sub(r"[^\w]", "", clean_term)
        if w_c in _IPA_DICT_UK:
            uk_ipa = _IPA_DICT_UK[w_c]
            return _to_us_ipa(uk_ipa) if accent == "en-us" else uk_ipa

        return _rule_based_english(w_c, accent)

    # 7. Diğer tüm dünya dilleri için doğrudan fonetik gösterge
    return f"/{clean_term}/"
