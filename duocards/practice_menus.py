"""Kullanıcının kendi kartlarıyla çalışan beş ana uygulama menüsü."""
MENU_TITLES = {
    'sentence_memory': ['Cümle Hafızası', 'Sentence Memory', 'Satzspeicher', 'Banco de Frases'],
    'writing': ['Yazarak Hatırla', 'Written Recall', 'Schriftliches Erinnern', 'Recuerdo Escrito'],
    'mistakes': ['Hatalarım', 'My Mistakes', 'Meine Fehler', 'Mis Errores'],
    'favorites': ['Favoriler', 'Favorites', 'Favoriten', 'Favoritos'],
    'shadowing': ['Taklit', 'Shadowing', 'Nachsprechen', 'Repetición Oral'],
    'dictation': ['Dinleme', 'Listening', 'Hören', 'Escucha'],
    'cloze': ['Boşluk Doldurma', 'Fill in the Blank', 'Lückentext', 'Completar Huecos'],
}
NEW_CORE_MENUS = [dict(id=key, setting_key=f'menu_visible_{key}', default=True,
                       icon=key,
                       titles=dict(zip(('tr','en','de','es'),titles)), view_name=key)
                  for key,titles in MENU_TITLES.items() if key not in ('dictation','cloze')]


def title(key, lang):
    return MENU_TITLES[key][('tr','en','de','es').index(lang) if lang in ('tr','en','de','es') else 1]
