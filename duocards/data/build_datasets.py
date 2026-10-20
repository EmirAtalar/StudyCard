#!/usr/bin/env python3
"""
Study Card - 15 Dünya Dili Veri Tabanı Ana Üretim Betiği
Bu betik çalıştırıldığında 15 dünya dili için 1000'er adetlik
tüm veri setlerini oluşturur ve doğrular.
"""

import os
import sys

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DATA_DIR)

from generate_datasets import generate_german, generate_english, save_and_verify
from gen_romance import generate_french, generate_spanish, generate_italian, generate_portuguese
from gen_germanic import generate_dutch, generate_swedish
from gen_east_asia import generate_chinese, generate_japanese, generate_korean
from gen_others import generate_russian, generate_arabic, generate_hindi, generate_turkish

def build_all():
    print("=" * 60)
    print("Study Card - 15 Dünya Dili Veri Tabanı Üretimi Başlıyor...")
    print("=" * 60)
    
    # 1. Almanca
    save_and_verify("de_articles.json", generate_german())
    # 2. İngilizce
    save_and_verify("en_verbs.json", generate_english())
    # 3. Fransızca
    save_and_verify("fr_verbs.json", generate_french())
    # 4. İspanyolca
    save_and_verify("es_verbs.json", generate_spanish())
    # 5. İtalyanca
    save_and_verify("it_verbs.json", generate_italian())
    # 6. Portekizce
    save_and_verify("pt_verbs.json", generate_portuguese())
    # 7. Felemenkçe
    save_and_verify("nl_articles.json", generate_dutch())
    # 8. İsveççe
    save_and_verify("sv_articles.json", generate_swedish())
    # 9. Çince
    save_and_verify("zh_words.json", generate_chinese())
    # 10. Japonca
    save_and_verify("ja_words.json", generate_japanese())
    # 11. Korece
    save_and_verify("ko_words.json", generate_korean())
    # 12. Rusça
    save_and_verify("ru_words.json", generate_russian())
    # 13. Arapça
    save_and_verify("ar_words.json", generate_arabic())
    # 14. Hintçe
    save_and_verify("hi_words.json", generate_hindi())
    # 15. Türkçe
    save_and_verify("tr_words.json", generate_turkish())
    
    print("=" * 60)
    print("Tebrikler! 15 Dilin tamamı (her biri minimum 1000 kayıt) başarıyla hazırlandı.")
    print("=" * 60)

if __name__ == "__main__":
    build_all()
