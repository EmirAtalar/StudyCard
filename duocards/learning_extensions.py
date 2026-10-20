"""Örnek cümle ve anlam testi içeren, gündelik kullanıma yönelik dil paketleri."""

COLUMN_TITLES = {
    'tr': ['Kelime / Kalıp', 'Bağlam / İpucu', 'Örnek Cümle'],
    'en': ['Word / Phrase', 'Context / Tip', 'Example Sentence'],
    'de': ['Wort / Ausdruck', 'Kontext / Hinweis', 'Beispielsatz'],
    'es': ['Palabra / Expresión', 'Contexto / Consejo', 'Frase de Ejemplo'],
}

_PACKS = [
    ('en_phrasal',
     ['Phrasal Verbs: Günlük Kullanım', 'Phrasal Verbs: Everyday Use',
      'Phrasal Verbs: Alltag', 'Phrasal Verbs: Uso Cotidiano']),
    ('en_confusing_words',
     ['Karıştırılan İngilizce Kelimeler', 'Commonly Confused Words',
      'Häufig Verwechselte Wörter', 'Palabras que se Confunden']),
]

LEARNING_EXTENSIONS = [
    {
        'id': identifier,
        'icon': identifier,
        'setting_key': f'plugin_{identifier}',
        'default': False,
        'lang_code': 'EN',
        'titles': dict(zip(('tr', 'en', 'de', 'es'), names)),
        'nav_names': dict(zip(('tr', 'en', 'de', 'es'), names)),
        'badges': {
            'tr': ('26 Kelime / 13 Çift / Test' if identifier=='en_confusing_words' else '25 Kalıp / Örnek / Test'),
            'en': ('26 Words / 13 Pairs / Quiz' if identifier=='en_confusing_words' else '25 Entries / Examples / Quiz'),
            'de': ('26 Wörter / 13 Paare / Quiz' if identifier=='en_confusing_words' else '25 Einträge / Beispiele / Quiz'),
            'es': ('26 Palabras / 13 Pares / Test' if identifier=='en_confusing_words' else '25 Entradas / Ejemplos / Test'),
        },
        'badge_color': '#a78bfa',
        'view_name': f'ext_{identifier}',
        'dataset_file': f'{identifier}.json',
        'term_col': COLUMN_TITLES['tr'][0],
        'attr_col': COLUMN_TITLES['tr'][1],
        'extra_col': COLUMN_TITLES['tr'][2],
        'column_titles': COLUMN_TITLES,
        'filters': [],
    }
    for identifier, names in _PACKS
]
