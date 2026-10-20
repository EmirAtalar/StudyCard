"""
Study Card - Minimalist Tek Renk (Zümrüt Yeşili #10b981) Vektör Simge Motoru
Tüm menü ve arayüz simgelerini modern, tutarlı ve minimalist SVG vektörleri olarak üretir.
"""

from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize

# Minimalist, modern ve tutarlı SVG vektörleri (Tümü aynı zümrüt yeşili #10b981 tonunda)
_SVG_TEMPLATES = {
    # 1. Çalış (Study) - Aralıklı Tekrar & Ezber Flashcard
    "study": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="6" width="14" height="15" rx="3" ry="3"></rect>
        <path d="M7 2.5h11a3 3 0 0 1 3 3v12"></path>
        <line x1="6" y1="11" x2="12" y2="11"></line>
        <line x1="6" y1="15" x2="10" y2="15"></line>
    </svg>''',

    # 2. Manuel Kart Ekle (Add Card) - Kart ve Artı Simgesi
    "add": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="4" ry="4"></rect>
        <line x1="12" y1="8" x2="12" y2="16"></line>
        <line x1="8" y1="12" x2="16" y2="12"></line>
    </svg>''',

    # 3. Kütüphane (Library) - Açık Kitap
    "library": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
    </svg>''',

    # 4. Desteler (Decks) - Katmanlı Kart Desteleri
    "decks": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
        <polyline points="2 17 12 22 22 17"></polyline>
        <polyline points="2 12 12 17 22 12"></polyline>
    </svg>''',

    # 5. İstatistikler (Stats) - Sütun Grafik
    "stats": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"></line>
        <line x1="12" y1="20" x2="12" y2="4"></line>
        <line x1="6" y1="20" x2="6" y2="14"></line>
        <line x1="2" y1="20" x2="22" y2="20"></line>
    </svg>''',

    # 6. İçe / Dışa Aktar (Import/Export) - Aktarım Simgesi
    "import": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M7 10l5 5 5-5"></path>
        <path d="M12 15V3"></path>
        <path d="M20 21H4"></path>
    </svg>''',

    # 7. Yapay Zeka (AI) - AI Sparkle Yıldızları
    "ai": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2c0 4.5-3.5 8-8 8 4.5 0 8 3.5 8 8 0-4.5 3.5-8 8-8-4.5 0-8-3.5-8-8z"></path>
        <path d="M19 3c0 1.5-1 2.5-2.5 2.5 1.5 0 2.5 1 2.5 2.5 0-1.5 1-2.5 2.5-2.5-1.5 0-2.5-1-2.5-2.5z"></path>
    </svg>''',

    # 8. Ayarlar (Settings) - Yeşil Dişli / Çark
    "settings": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
    </svg>''',

    # 9. Kuralsız Fiiller (Irregular Verbs) - Fiil Döngüsü
    "verbs": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"></polyline>
        <polyline points="1 20 1 14 7 14"></polyline>
        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
    </svg>''',

    # 10. Zamanlayıcı & Kronometre (Timer & Stopwatch)
    "timer": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="13" r="8"></circle>
        <polyline points="12 9 12 13 15 13"></polyline>
        <line x1="12" y1="2" x2="12" y2="5"></line>
        <line x1="9" y1="2" x2="15" y2="2"></line>
    </svg>''',

    # 11. Saat (Clock)
    "clock": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
    </svg>''',

    # 12. Eklentiler (Extensions / Puzzle)
    "extensions": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20.5 11H19V7a2 2 0 0 0-2-2h-4V3.5a2.5 2.5 0 0 0-5 0V5H4a2 2 0 0 0-2 2v3.8h1.5a2.5 2.5 0 0 1 0 5H2V20a2 2 0 0 0 2 2h3.8v-1.5a2.5 2.5 0 0 1 5 0V22H17a2 2 0 0 0 2-2v-4h1.5a2.5 2.5 0 0 0 0-5z"></path>
    </svg>''',

    # 13. Almanca Artikeller (Articles / Der Die Das)
    "articles": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
    </svg>''',

    # 14. Fransızca Fiiller
    "verbs_fr": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
        <circle cx="13" cy="10" r="3"></circle>
    </svg>''',

    # 15. İspanyolca Fiiller
    "verbs_es": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polygon points="10 8 16 12 10 16 10 8"></polygon>
    </svg>''',

    # 16. Ses / Telaffuz (Audio)
    "audio": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
    </svg>''',

    # 17. Dünya / Dil (Globe)
    "globe": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="2" y1="12" x2="22" y2="12"></line>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
    </svg>''',

    # 18. Bildirim (Bell)
    "bell": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
    </svg>''',

    # 19. Masaüstü / Widget (Desktop)
    "desktop": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
        <line x1="8" y1="21" x2="16" y2="21"></line>
        <line x1="12" y1="17" x2="12" y2="21"></line>
    </svg>''',

    # 20. Hedef / Çalışma (Target)
    "target": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <circle cx="12" cy="12" r="6"></circle>
        <circle cx="12" cy="12" r="2"></circle>
    </svg>''',

    # 21. Onay / Kaydet (Check)
    "check": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"></polyline>
    </svg>''',

    # 22. Kelime Eşleştirme (Match Game) - Şimşek / Hızlı Refleks
    "match": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
    </svg>''',

    # 23. Yıldız & Favori (Star)
    "star": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
    </svg>''',

    "star_filled": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#f59e0b" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
    </svg>''',

    # Seri & Ateş (Flame)
    "flame": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path>
    </svg>''',

    # Hafıza İpucu (Bulb)
    "bulb": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#eab308" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 18h6"></path><path d="M10 22h4"></path><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5.76.76 1.23 1.52 1.41 2.5"></path>
    </svg>''',

    # Ters Çevirme (Reverse)
    "reverse": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path>
    </svg>''',

    # Klavye / Aktif Hatırlama (Keyboard)
    "keyboard": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6" y2="8"></line><line x1="10" y1="8" x2="10" y2="8"></line><line x1="14" y1="8" x2="14" y2="8"></line><line x1="18" y1="8" x2="18" y2="8"></line><line x1="6" y1="12" x2="6" y2="12"></line><line x1="10" y1="12" x2="10" y2="12"></line><line x1="14" y1="12" x2="14" y2="12"></line><line x1="18" y1="12" x2="18" y2="12"></line><line x1="7" y1="16" x2="17" y2="16"></line>
    </svg>''',

    # Cümle Seslendirme (Volume)
    "volume": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
    </svg>''',

    # 24. Dinleme & Dikte Pratiği (Dictation / Audio Coach) - Kulaklık & Ses
    "dictation": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 18v-6a9 9 0 0 1 18 0v6"></path>
        <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"></path>
    </svg>''',

    # Cümle Hafızası - Yer imi olan konuşma balonu
    "sentence_memory": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 3h1a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H8l-6 3V5a2 2 0 0 1 2-2h9"></path>
        <path d="M13 3h6v9l-3-2-3 2z"></path>
        <path d="M6 8h3M6 13h3"></path>
    </svg>''',

    # Yazarak Hatırla - Kalem
    "writing": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m16 3 5 5-12 12-7 2 2-7z"></path>
        <path d="m13 6 5 5M4 15l5 5"></path>
    </svg>''',

    # Hatalarım - Uyarı üçgeni
    "mistakes": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10.3 3.5a2 2 0 0 1 3.4 0l8 14.5a2 2 0 0 1-1.7 3H4a2 2 0 0 1-1.7-3z"></path>
        <path d="M12 9v4M12 17h.01"></path>
    </svg>''',

    # Favoriler - Kalp
    "favorites": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z"></path>
    </svg>''',

    # Günlük Meydan Okuma - Kupa
    "shadowing": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M7 3h10v7a5 5 0 0 1-10 0z"></path>
        <path d="M7 5H3v3a4 4 0 0 0 4 4M17 5h4v3a4 4 0 0 1-4 4M12 15v6M8 21h8"></path>
    </svg>''',

    # Phrasal Verbs - Dallanan oklar
    "en_phrasal": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 21v-6M5 9V5M19 9V5M5 9a7 7 0 0 0 14 0"></path>
        <path d="m2 8 3-3 3 3M16 8l3-3 3 3"></path>
    </svg>''',

    # Doğal Kelime Birliktelikleri - Zincir halkaları
    "en_collocations": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M10 13a5 5 0 0 0 7 .2l4-4a5 5 0 0 0-7-7l-2 2M14 11a5 5 0 0 0-7-.2l-4 4a5 5 0 0 0 7 7l2-2"></path>
    </svg>''',

    # Günlük Konuşma Kalıpları - İki konuşma balonu
    "en_daily_phrases": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 3h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H7l-5 3V4a1 1 0 0 1 1-1z"></path>
        <path d="M20 9h1a1 1 0 0 1 1 1v12l-5-3H9a1 1 0 0 1-1-1v-1"></path>
        <path d="M6 7h6"></path>
    </svg>''',

    # İş ve E-posta İngilizcesi - Evrak çantası
    "en_workplace": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2"></rect>
        <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M2 12a24 24 0 0 0 20 0M12 12v4"></path>
    </svg>''',

    # Karıştırılan İngilizce Kelimeler - İki yönlü tabela
    "en_confusing_words": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2v2M12 9v3M12 17v5"></path>
        <path d="M4 4h14l3 2.5L18 9H4zM20 12H6l-3 2.5L6 17h14z"></path>
    </svg>''',

    # 25. Cümlede Boşluk Doldurma (Cloze Deletion) - Doküman ve Boşluk
    "cloze": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <line x1="8" y1="13" x2="16" y2="13"></line>
        <line x1="8" y1="17" x2="13" y2="17"></line>
    </svg>'''
}

_SVG_TEMPLATES.update({
    'maker': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m4 16 12-12a2.1 2.1 0 0 1 3 3L7 19l-4 1zM14 6l3 3M4 16l3 3"/></svg>',
    'table_grid': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 10h18M3 15h18M9 10v10M15 10v10"/></svg>',
    'gamepad': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 6h10c3 0 4 2 4.5 5l.5 6c.2 3-2.3 4-4 2l-3-3H9l-3 3c-1.7 2-4.2 1-4-2l.5-6C3 8 4 6 7 6z"/><path d="M6 10v5M3.5 12.5h5M15 10.5h.1M18 13h.1M10 6V3h4"/></svg>',
    'rocket': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 15c1-6 6-11 12-12 0 6-5 11-12 12zM9 9H5l-3 5 7 1 1 7 5-3v-4M6 17l-3 4 4-2"/><circle cx="16" cy="8" r="2"/></svg>',
    'bulb': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.8" stroke-linecap="round"><path d="M8 16c0-3-3-3-3-7a7 7 0 0 1 14 0c0 4-3 4-3 7zM8 19h8M10 22h4M12 9v7M9 9l3 3 3-3"/></svg>',
})

_PERSONAL_PATHS = {
    'pencil': '<path d="m4 16 12-12a2.1 2.1 0 0 1 3 3L7 19l-4 1zM14 6l3 3M4 16l3 3"/>',
    'headphones': '<path d="M4 13v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="11" width="4" height="9" rx="2"/><rect x="17" y="11" width="4" height="9" rx="2"/>',
    'microphone': '<rect x="8" y="2" width="8" height="13" rx="4"/><path d="M5 11v2a7 7 0 0 0 14 0v-2M12 20v2M8 22h8"/>',
    'music': '<path d="M9 18V5l11-2v13M9 9l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2"/><ellipse cx="17" cy="16" rx="3" ry="2"/>',
    'sound_wave': '<path d="M3 10v4M7 6v12M11 3v18M15 7v10M19 5v14M23 10v4"/>',
    'brain': '<path d="M12 4a3 3 0 0 0-6-1 4 4 0 0 0-3 7 4 4 0 0 0 1 7 4 4 0 0 0 8 3V4zm0 0a3 3 0 0 1 6-1 4 4 0 0 1 3 7 4 4 0 0 1-1 7 4 4 0 0 1-8 3M6 8l3 1M4 14l4-1M18 8l-3 1M20 14l-4-1"/>',
    'puzzle': '<path d="M4 3h6v2a2 2 0 1 0 4 0V3h6v6h-2a2 2 0 1 0 0 4h2v7h-6v-2a2 2 0 1 0-4 0v2H4v-7H2a2 2 0 1 1 0-4h2z"/>',
    'compass': '<circle cx="12" cy="12" r="9"/><path d="m16 8-3 5-5 3 3-5z"/>',
    'leaf': '<path d="M20 3C8 2 2 7 4 15c2 8 14 5 16-12zM4 20 15 9M9 15v-4M9 15h4"/>',
    'flower': '<circle cx="12" cy="10" r="3"/><path d="M10 7c-4-5 8-5 4 0 6-2 8 8 2 6 0 6-8 6-8 0-6 2-4-8 2-6zM12 16v6M12 20l5-3M12 21l-5-2"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/>',
    'moon': '<path d="M20 15A9 9 0 0 1 9 3a9 9 0 1 0 11 12z"/>',
    'cloud': '<path d="M7 18h12a4 4 0 0 0 0-8 7 7 0 0 0-13-1 4.5 4.5 0 0 0 1 9z"/>',
    'bolt': '<path d="m13 2-9 12h7l-1 8 10-13h-7z"/>',
    'heart': '<path d="M12 21 3 12C-2 5 7-1 12 6c5-7 14-1 9 6z"/>',
    'trophy': '<path d="M7 3h10v7a5 5 0 0 1-10 0zM7 5H3v3a4 4 0 0 0 4 4M17 5h4v3a4 4 0 0 1-4 4M12 15v6M8 21h8"/>',
    'medal': '<path d="m5 2 4 8M19 2l-4 8M8 2l4 7 4-7"/><circle cx="12" cy="15" r="6"/><path d="m12 12 1 2 2 1-2 1-1 2-1-2-2-1 2-1z"/>',
    'gem': '<path d="m3 8 4-5h10l4 5-9 13zM3 8h18M7 3l5 18 5-18M7 8l5-5 5 5"/>',
    'mountain': '<path d="m2 20 8-16 7 16zm12-7 3-6 6 13h-6M7 10l3 3 3-3"/>',
    'anchor': '<circle cx="12" cy="4" r="2"/><path d="M12 6v15M8 10h8M3 14c0 5 4 7 9 7s9-2 9-7M3 14l-2 3M3 14l3 2M21 14l2 3M21 14l-3 2"/>',
}
for _name, _paths in _PERSONAL_PATHS.items():
    _SVG_TEMPLATES[_name] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+_paths+'</svg>'

PERSONAL_ICONS = ('table_grid', 'gamepad', 'rocket', 'bulb', 'study', 'library', 'decks', 'target', 'globe', 'audio', 'star', 'flame') + tuple(_PERSONAL_PATHS)
PERSONAL_ICON_LABELS = dict(table_grid='Table', gamepad='Game', rocket='Rocket', bulb='Idea', study='Cards', library='Book', decks='Stack', target='Target', globe='World', audio='Sound', star='Star', flame='Flame', pencil='Pencil', headphones='Headphones', microphone='Microphone', music='Music', sound_wave='Sound wave', brain='Brain', puzzle='Puzzle', compass='Compass', leaf='Leaf', flower='Flower', sun='Sun', moon='Moon', cloud='Cloud', bolt='Lightning', heart='Heart', trophy='Trophy', medal='Medal', gem='Gem', mountain='Mountain', anchor='Anchor')

_ICON_CACHE = {}


def get_icon(name: str, size: int = 22, color: str = "#10b981") -> QIcon:
    """
    Belirtilen isim için minimalist zümrüt yeşili (#10b981) ve seçili durum için beyaz QIcon döndürür.
    """
    cache_key = f"{name}_{size}_{color}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    svg_data = _SVG_TEMPLATES.get(name)
    if not svg_data:
        return QIcon()

    # Normal durum (yeşil) ve Seçili durum (beyaz)
    svg_normal = svg_data.replace("#10b981", color)
    svg_active = svg_data.replace("#10b981", "#ffffff")

    from PyQt6.QtCore import QByteArray, Qt
    from PyQt6.QtGui import QPainter
    from PyQt6.QtSvg import QSvgRenderer
    def render(svg):
        pixmap = QPixmap(size*2, size*2)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        QSvgRenderer(QByteArray(svg.encode('utf-8'))).render(painter)
        painter.end()
        pixmap.setDevicePixelRatio(2)
        return pixmap
    pix_normal = render(svg_normal)
    pix_active = render(svg_active)

    icon = QIcon()
    icon.addPixmap(pix_normal, QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(pix_active, QIcon.Mode.Normal, QIcon.State.On)
    icon.addPixmap(pix_active, QIcon.Mode.Active, QIcon.State.On)
    _ICON_CACHE[cache_key] = icon
    return icon
