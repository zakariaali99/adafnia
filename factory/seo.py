from xml.etree.ElementTree import Element, SubElement, tostring
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from .views import public_data

@require_GET
def robots(request):
    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    return HttpResponse(f'User-agent: *\nAllow: /\nDisallow: /dashboard/\nDisallow: /admin/\nSitemap: {sitemap_url}\n', content_type='text/plain; charset=utf-8')

@require_GET
def sitemap(request):
    root = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    def add(path, modified=None):
        url = SubElement(root, 'url')
        SubElement(url, 'loc').text = request.build_absolute_uri(path)
        if modified:
            SubElement(url, 'lastmod').text = modified.isoformat()
    data = public_data()
    for lang in ('ar', 'en'):
        for route in ('', 'about/', 'products/', 'news/', 'projects/', 'quality/', 'resources/', 'contact/'):
            add(f'/{lang}/{route}')
        for section in ('products', 'news', 'projects'):
            for obj in data[section].prefetch_related(None).iterator():
                add(f'/{lang}/{section}/{obj.pk}/', obj.published_at.date() if section == 'news' else None)
    return HttpResponse(tostring(root, encoding='utf-8', xml_declaration=True), content_type='application/xml; charset=utf-8')
