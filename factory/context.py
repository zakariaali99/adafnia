import re

from .models import SiteSettings, Branch, Category
from .strings import STRINGS


def site_context(request):
    lang = getattr(request, 'site_lang', 'ar')
    parts = request.path.split('/', 2)
    current = '/' + parts[2] if len(parts) > 2 and parts[1] in ('ar', 'en') else request.path
    settings = SiteSettings.objects.first() or SiteSettings()
    other = 'en' if lang == 'ar' else 'ar'
    return {'lang': lang, 'is_ar': lang == 'ar', 'prefix': '/' + lang,
            'current_path': current.lstrip('/'), 'nav_path': current,
            'other_lang_url': f'/{other}{current}',
            'settings': settings,
            'wa_number': re.sub(r'\D', '', settings.whatsapp or settings.phone or ''),
            'branches': Branch.objects.filter(is_factory=False), 'categories': Category.objects.filter(products__is_published=True).distinct(),
            't': STRINGS.get(lang, STRINGS['ar'])}
