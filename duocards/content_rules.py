"""Shared rules for duplicate words and useful, contextual usage sentences."""
import re
import unicodedata


def term_key(term):
    return ' '.join(unicodedata.normalize('NFKC', term or '').casefold().replace('\u0307', '').split())


def useful_sentence(term, sentence, lang='en'):
    from duocards.languages import get_language_code
    lang = get_language_code(lang)
    sentence = ' '.join((sentence or '').split())
    if not sentence or len(sentence) > 500 or sentence.endswith(('...', '…')):
        return False
    from duocards.sentence_memory import term_pattern
    pattern = term_pattern(term, lang)
    if not pattern.search(sentence):
        return False
    context = pattern.sub(' ', sentence)
    if lang in ('zh', 'zh-tw', 'ja'):
        return len(re.sub(r'[\W\d_]', '', sentence)) >= 12 and len(re.sub(r'[\W\d_]', '', context)) >= 6
    return len(re.findall(r"[^\W_]+(?:['’][^\W_]+)*", sentence)) >= 8 and len(re.findall(r'[^\W_]+', context)) >= 4
