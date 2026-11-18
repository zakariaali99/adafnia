import re

from django import template
register = template.Library()

PHONE_RE = re.compile(r'(?:\+?218[\s-]?|0)9\d[\s-]?\d{3}[\s-]?\d{4}')
WORD_RE = re.compile(r'[^\W\d_]', re.UNICODE)


def _digits(value):
    return re.sub(r'\D', '', value)


@register.filter
def phones(branch):
    """Every distinct Libyan mobile number on a branch (phone field + description), formatted 091 234 5678."""
    found, seen = [], set()
    sources = [branch.phone or '', branch.description_ar or '', branch.description_en or '']
    for match in PHONE_RE.findall(' '.join(sources)):
        digits = _digits(match)
        local = '0' + digits[3:] if digits.startswith('218') else digits
        if local not in seen:
            seen.add(local)
            found.append(f'{local[:3]} {local[3:6]} {local[6:]}')
    return found


@register.filter
def tel(phone):
    """'091 234 5678' -> '+218912345678' for tel: links."""
    digits = _digits(phone)
    return '+218' + digits[1:] if digits.startswith('0') else '+' + digits


@register.filter
def standard(title):
    """'ISO 9001:2015' -> 'ISO 9001' for compact badges."""
    match = re.match(r'\s*(ISO\s*\d+)', title or '')
    return match.group(1) if match else title


@register.filter
def has_words(text):
    """True when text holds more than phone numbers and separators."""
    return bool(WORD_RE.search(PHONE_RE.sub('', text or '')))

ARABIC_RE = re.compile(r'[\u0600-\u06FF]')
# Latin/number runs such as 23.03.530-QM, 2026-05-10, ISO 9001:2015 or PE100.
MIXED_RE = re.compile(r'(?<![\w\u2066])([A-Za-z0-9][A-Za-z0-9.:/+_-]*[A-Za-z0-9])(?![\w])')


def isolate_ltr(text):
    """In Arabic text, wrap Latin/number runs in LRI…PDI so the bidi algorithm cannot flip them
    (otherwise «رقم الشهادة 23.03.530-QM» displays as QM-23.03.530). Invisible, safe in attributes."""
    if not text or not ARABIC_RE.search(text):
        return text

    def wrap(match):
        token = match.group(1)
        mixed = re.search(r'[A-Za-z]', token) and re.search(r'\d', token)
        if mixed or re.search(r'\d[.:/-]\d', token):
            return '\u2066' + token + '\u2069'
        return token
    return MIXED_RE.sub(wrap, text)


@register.filter
def bidi(text):
    return isolate_ltr(text)


@register.simple_tag
def translated(obj, field, lang='ar'):
    value = getattr(obj, f'{field}_{lang}', '') or getattr(obj, f'{field}_ar', '') or getattr(obj, f'{field}_en', '')
    return isolate_ltr(value) if isinstance(value, str) else value

@register.filter
def field(obj, name):
    return (obj, name)

@register.filter
def tr(obj, lang):
    if isinstance(obj, tuple):
        return translated(obj[0], obj[1], lang)
    return translated(obj, 'title', lang)
