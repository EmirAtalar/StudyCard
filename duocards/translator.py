"""
Study Card - Çok Dilli Çeviri Motoru (Universal Multilingual Translation Helper)
Kullanıcı manuel kart eklerken:
1. Kaynak Dil İngilizce ise doğrudan Cambridge Akademik Sözlüğü üzerinden en doğal çeviriyi çeker.
2. Diğer tüm dünya dilleri (Almanca, Fransızca, İspanyolca, İtalyanca, Rusça, Japonca vb.) arasında
   hızlı, güvenilir ve çift yönlü çeviri önerisi sunar.
"""

import urllib.request
import urllib.parse
import json
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from PyQt6.QtCore import QThread, pyqtSignal

from duocards.languages import get_language_code, get_cambridge_slug, normalize_string


def fetch_cambridge_translation(text: str, target_lang: str = "Türkçe",
                                part_of_speech: str = "") -> Optional[Dict[str, Any]]:
    """
    Cambridge Dictionary İngilizce-(Kullanıcının Seçtiği Dil) sözlüğünden
    anlam ve çevirileri doğrudan çeker.
    """
    clean_term = text.strip()
    if not clean_term:
        return None

    lang_slug = get_cambridge_slug(target_lang)
    slug = urllib.parse.quote(clean_term.lower().replace(" ", "-"))
    url = f"https://dictionary.cambridge.org/dictionary/english-{lang_slug}/{slug}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode("utf-8", errors="replace")

        soup = BeautifulSoup(html, "html.parser")
        nodes = soup.find_all("span", class_=re.compile(r"\btrans\b"))
        trans_list: List[str] = []
        pos_str = ""
        for node in nodes:
            # A page can contain noun, verb and nested phrasal-verb entries.
            # Read the POS from the closest entry containing this translation.
            entry = node.find_parent(class_=re.compile(
                r"\b(?:entry-body__el|phrasal-verb-block|idiom-block|phrase-block)\b"))
            if entry is None:
                continue
            pos_node = entry.select_one(".pos")
            raw_pos = pos_node.get_text(" ", strip=True).lower() if pos_node else ""
            if not raw_pos:
                classes = entry.get("class", [])
                raw_pos = next((pos for block, pos in (
                    ("phrasal-verb-block", "phrasal verb"),
                    ("idiom-block", "idiom"), ("phrase-block", "phrase")
                ) if block in classes), "")
            if part_of_speech and part_of_speech != "word":
                if not raw_pos or detect_category(text, raw_pos=raw_pos) != part_of_speech:
                    continue
            txt = node.get_text(strip=True)
            txt = re.sub(r"\s*\[.*?\]", "", txt).strip()
            if txt and txt not in trans_list:
                if not trans_list:
                    pos_str = raw_pos
                trans_list.append(txt)

        if trans_list:
            return {
                "text": text,
                "translation": trans_list[0],
                "translations": trans_list,
                "pos": pos_str,
                "source": "Cambridge Dictionary",
                "error": None
            }
    except Exception:
        pass
    return None


def detect_category(
    term: str,
    definition: str = "",
    source_lang: str = "en",
    target_lang: str = "tr",
    raw_pos: str = ""
) -> str:
    """
    Kelime ve çeviri önerisine göre en uygun kategori anahtarını otomatik algılar:
    'word', 'noun', 'verb', 'phrasal_verb', 'adjective', 'adverb', 'idiom', 'phrase', 'article', 'conjunction'
    """
    raw = (raw_pos or "").lower().strip()
    if "phrasal verb" in raw:
        return "phrasal_verb"
    if "idiom" in raw:
        return "idiom"
    if "phrase" in raw:
        return "phrase"
    if "noun" in raw:
        return "noun"
    if "adjective" in raw or "adj" in raw:
        return "adjective"
    if "adverb" in raw or "adv" in raw:
        return "adverb"
    if "verb" in raw:
        return "verb"
    if "article" in raw:
        return "article"
    if "conjunction" in raw or "preposition" in raw or "prep" in raw:
        return "conjunction"

    t_clean = term.strip().lower()
    tokens = t_clean.split()
    first_def = definition.split(",")[0].split("/")[0].split(";")[0].strip().lower()

    # 1. Artikel kontrolü (Almanca vb.)
    if t_clean.startswith(("der ", "die ", "das ", "ein ", "eine ")):
        return "article"

    # 2. Deyim / İfade kontrolü (3 veya daha fazla kelime, deyim belirteçleri)
    if len(tokens) >= 3 or "..." in term or any(w in tokens for w in ("sb", "sth", "someone", "something", "one's", "birini", "birşeyi")):
        return "idiom"

    # 3. Phrasal verb kontrolü (2 kelimeli veya edatlı fiil öbekleri)
    particles = {
        "up", "down", "in", "out", "off", "on", "away", "back", "over",
        "by", "around", "through", "along", "about", "across", "after",
        "ahead", "apart", "aside", "forward", "into"
    }
    if len(tokens) >= 2 and tokens[1] in particles:
        return "phrasal_verb"

    # 4. Mastar fiil ('to ...')
    if t_clean.startswith("to ") and len(tokens) >= 2:
        return "verb"

    # 5. Tanım Türkçe ise mastar eki kontrolü (-mek / -mak)
    src_code = get_language_code(source_lang).lower()
    tgt_code = get_language_code(target_lang).lower()
    if tgt_code == "tr":
        if first_def not in ("ekmek", "çakmak", "kaymak", "yemek", "ilmek"):
            if first_def.endswith(("mek", "mak", "mek.", "mak.")):
                return "verb"

    # 6. Zarf (-ly, -mente, -ment)
    if t_clean.endswith("ly") and len(t_clean) > 3:
        return "adverb"
    if t_clean.endswith("mente") and len(t_clean) > 5:
        return "adverb"

    # 7. Sıfat takıları
    if t_clean.endswith(("able", "ible", "ful", "less", "ous", "ive", "ish", "istic")):
        return "adjective"

    # 8. 2 kelimeli kalıp ifade
    if len(tokens) == 2:
        return "phrase"

    # 9. Almanca isim kontrolü (İsimler büyük harfle başlar)
    if src_code == "de":
        stripped = term.strip()
        if stripped and stripped[0].isupper():
            return "noun"

    return "noun"


def fetch_mymemory_translation(text: str, source_lang: str = "İngilizce", target_lang: str = "Türkçe") -> Dict[str, Any]:
    """
    MyMemory Evrensel Çok Dilli Çeviri Motoru.
    Dünyadaki tüm diller arasında (örn. Almanca -> Türkçe, Fransızca -> Türkçe vb.) çeviri yapar.
    """
    result = {
        "text": text,
        "translation": "",
        "translations": [],
        "source": "MyMemory Universal",
        "error": None
    }
    clean_term = text.strip()
    if not clean_term:
        return result

    src_code = get_language_code(source_lang)
    tgt_code = get_language_code(target_lang)

    # Aynı dil seçildiyse doğrudan döner
    if src_code == tgt_code:
        result["translation"] = clean_term
        result["translations"] = [clean_term]
        return result

    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(clean_term)}&langpair={src_code}|{tgt_code}"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))

        resp_data = data.get("responseData", {})
        translated_text = resp_data.get("translatedText", "").strip()

        # Ek çeviri alternatifleri
        matches = data.get("matches", [])
        trans_set = []
        if translated_text:
            trans_set.append(translated_text)

        for m in matches:
            t_match = m.get("translation", "").strip()
            if t_match and t_match not in trans_set and not t_match.startswith("MYMEMORY"):
                trans_set.append(t_match)

        if trans_set:
            result["translation"] = trans_set[0]
            result["translations"] = trans_set
        else:
            result["error"] = "Çeviri bulunamadı."
    except Exception as e:
        result["error"] = f"Bağlantı hatası: {str(e)}"

    return result


def fetch_cambridge_translation_sync(text: str, target_lang: str = "Türkçe",
                                     source_lang: str = "İngilizce",
                                     part_of_speech: str = "") -> Dict[str, Any]:
    """
    Tüm diller için en uygun çeviriyi bulur.
    Kaynak İngilizce ise önce Cambridge'i dener; bulunamazsa veya farklı dil çiftiyse
    evrensel çeviri motoruna yönlendirir.
    """
    src_code = get_language_code(source_lang)
    tgt_code = get_language_code(target_lang)
    category = part_of_speech if part_of_speech != "word" else ""

    # 1. Eğer İngilizce -> Hedef Dil ise öncelikle Cambridge
    if src_code == "en":
        cambridge_res = fetch_cambridge_translation(text, target_lang, category)
        if cambridge_res and cambridge_res.get("translation"):
            return cambridge_res

    # 2. Evrensel motor (Tüm diller: Almanca, Fransızca, İspanyolca, İtalyanca vb.)
    result = fetch_mymemory_translation(text, source_lang, target_lang)
    if not category or not result.get("translation"):
        return result

    # MyMemory has no POS metadata. Turkish infinitives let us distinguish
    # noun/verb alternatives; other unverified senses must not fill the field.
    matching = []
    if tgt_code == "tr" and category in ("noun", "verb"):
        for translation in result.get("translations", []):
            for meaning in re.split(r"[,;/]", translation):
                meaning = meaning.strip()
                if meaning and detect_category("", meaning, target_lang="tr") == category and meaning not in matching:
                    matching.append(meaning)
    if matching:
        result.update(translation=matching[0], translations=matching, pos=category)
    else:
        result.update(translation="", translations=[], error="part_of_speech_not_found")
    return result


# Geriye dönük uyumluluk
fetch_translation_sync = fetch_cambridge_translation_sync


class TranslationWorker(QThread):
    result_ready = pyqtSignal(dict)

    def __init__(self, text: str, target_lang: str = "Türkçe", source_lang: str = "İngilizce",
                 part_of_speech: str = "", parent=None):
        super().__init__(parent)
        self.text = text
        self.target_lang = target_lang
        self.source_lang = source_lang
        self.part_of_speech = part_of_speech

    def run(self):
        res = fetch_cambridge_translation_sync(self.text, self.target_lang, self.source_lang,
                                               self.part_of_speech)
        self.result_ready.emit(res)
