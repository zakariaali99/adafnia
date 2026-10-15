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

@register.simple_tag
def translated(obj, field, lang='ar'):
    return getattr(obj, f'{field}_{lang}', '') or getattr(obj, f'{field}_ar', '') or getattr(obj, f'{field}_en', '')

@register.filter
def field(obj, name):
    return (obj, name)

@register.filter
def tr(obj, lang):
    if isinstance(obj, tuple):
        return translated(obj[0], obj[1], lang)
    return translated(obj, 'title', lang)
