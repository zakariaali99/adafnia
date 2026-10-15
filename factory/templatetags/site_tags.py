from django import template
register = template.Library()

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
