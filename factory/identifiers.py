import re

MAX_ID = 9223372036854775807

def parse_id(value):
    """Accept only positive ASCII decimal IDs that fit a signed 64-bit PK."""
    if not isinstance(value, str) or not 1 <= len(value) <= 19:
        raise ValueError('Invalid ID')
    if not value.isascii() or not value.isdecimal():
        raise ValueError('Invalid ID')
    number = int(value)
    if not 1 <= number <= MAX_ID:
        raise ValueError('Invalid ID')
    return number

def id_or_slug(value, id_field='pk', slug_field='slug'):
    """Keep bounded ASCII slugs distinct from invalid numeric identifiers."""
    if isinstance(value, str) and value[:1] in ('+', '-') and value[1:].isdecimal():
        raise ValueError('Invalid signed ID')
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return {id_field: parse_id(value)}
    if isinstance(value, str) and len(value) <= 50 and re.fullmatch(r'[A-Za-z0-9_-]+', value):
        return {slug_field: value}
    raise ValueError('Invalid ID or slug')
