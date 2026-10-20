"""Stable menu identities for user tables and games; preferences travel in backups."""
from duocards import custom_tables, custom_games
from duocards.settings import settings


def menu_key(kind, ident):
    return f'personal_menu_{kind}_{ident}'


def in_menu(kind, ident):
    return bool(settings.get(menu_key(kind, ident), False))


def documents():
    return [('table', table) for table in custom_tables.list_tables()] + [('game', game) for game in custom_games.list_games()]
