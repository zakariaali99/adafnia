from .models import SiteSettings, Branch, Category

def site_context(request):
    lang = getattr(request, 'site_lang', 'ar')
    parts = request.path.split('/', 2)
    current = '/' + parts[2] if len(parts) > 2 and parts[1] in ('ar', 'en') else request.path
    return {'lang': lang, 'is_ar': lang == 'ar', 'prefix': '/' + lang,
            'current_path': current.lstrip('/'), 'nav_path': current,
            'settings': SiteSettings.objects.first() or SiteSettings(),
            'branches': Branch.objects.filter(is_factory=False), 'categories': Category.objects.filter(products__is_published=True).distinct()}
