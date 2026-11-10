import hashlib
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone, translation
from django.core.paginator import Paginator
from .models import Product, ProductVariant, NewsArticle, Project, Certificate, Resource, SubmissionThrottle, SiteSettings
from .forms import EnquiryForm
from .identifiers import parse_id, id_or_slug
from .strings import STRINGS


def _str(value):
    return None if value is None else str(value)

def public_data():
    return {'products': Product.objects.filter(is_published=True).select_related('category').prefetch_related(Prefetch('variants', queryset=ProductVariant.objects.filter(approved=True))),
            'news': NewsArticle.objects.filter(status='published', published_at__lte=timezone.now()),
            'projects': Project.objects.filter(is_published=True),
            'certificates': Certificate.objects.filter(is_active=True).filter(Q(expires_on__gte=timezone.localdate()) | Q(expires_on__isnull=True)),
            'archived_certificates': Certificate.objects.filter(Q(is_active=False) | Q(expires_on__lt=timezone.localdate())),
            'resources': Resource.objects.all()}

def allow_submission(request, namespace='contact', limit=5, window=3600):
    # REMOTE_ADDR is deliberately used instead of trusting client-supplied forwarding headers.
    key = hashlib.sha256((namespace + ':' + settings.SECRET_KEY + request.META.get('REMOTE_ADDR', '')).encode()).hexdigest()
    with transaction.atomic():
        bucket, _ = SubmissionThrottle.objects.get_or_create(key=key)
        bucket = SubmissionThrottle.objects.select_for_update().get(pk=bucket.pk)
        now = timezone.now()
        if bucket.started_at < now - timedelta(seconds=window):
            bucket.started_at, bucket.count = now, 0
        allowed = bucket.count < limit
        if allowed:
            bucket.count += 1
            bucket.save()
        return allowed

def page(request, lang, page='home', slug=None):
    with translation.override(lang if lang in ('ar', 'en') else 'ar'):
        return localized_page(request, lang, page, slug)

def localized_page(request, lang, page='home', slug=None):
    if lang not in ('ar', 'en'):
        raise Http404
    request.site_lang = lang
    data = public_data()
    initial = {}
    product_id = request.GET.get('product', '')
    try:
        parsed_product_id = parse_id(product_id) if product_id else None
        variant_id = request.GET.get('variant', '')
        parsed_variant_id = parse_id(variant_id) if variant_id else None
    except ValueError:
        return JsonResponse({'error': 'Invalid product or variant ID'}, status=400)
    if parsed_product_id is not None:
        selected_product = Product.objects.filter(pk=parsed_product_id, is_published=True).first()
        if selected_product:
            initial['product'] = selected_product.pk
    if page == 'contact' and parsed_variant_id is not None:
        variant_qs = ProductVariant.objects.filter(pk=parsed_variant_id, approved=True, product__is_published=True).select_related('product')
        if product_id:
            variant_qs = variant_qs.filter(product_id=initial.get('product', 0))
        variant = variant_qs.first()
        if variant:
            initial['product'] = variant.product_id
            title = (variant.product.title_en or variant.product.title_ar) if lang == 'en' else variant.product.title_ar
            dimensions = [('diameter_mm', 'Diameter (mm)', 'القطر (مم)'), ('pressure_bar', 'Pressure (bar)', 'الضغط (بار)'), ('sdr', 'SDR', 'SDR'), ('wall_mm', 'Wall (mm)', 'السماكة (مم)'), ('weight_kg_m', 'Weight (kg/m)', 'الوزن (كجم/م)'), ('length_m', 'Length (m)', 'الطول (م)')]
            initial['message'] = title + '\n' + '\n'.join(f'{en if lang == "en" else ar}: {getattr(variant, field).normalize():f}' for field, en, ar in dimensions if getattr(variant, field) is not None)
            initial['subject'] = 'Request a quote' if lang == 'en' else 'طلب عرض سعر'
    data['form'] = EnquiryForm(lang=lang, initial=initial)
    if page.endswith('_detail'):
        key = {'product_detail': 'products', 'news_detail': 'news', 'project_detail': 'projects'}[page]
        try:
            lookup = id_or_slug(slug)
        except ValueError:
            raise Http404
        obj = get_object_or_404(data[key], **lookup)
        data.update({'object': obj, key.rstrip('s') if key != 'news' else 'article': obj})
        if key == 'products':
            data['product'] = obj
            data['variants'] = obj.variants.filter(approved=True)
            data['diameters'] = data['variants'].order_by('diameter_mm').values_list('diameter_mm', flat=True).distinct()
            data['pressures'] = data['variants'].exclude(pressure_bar__isnull=True).order_by('pressure_bar').values_list('pressure_bar', flat=True).distinct()
            data['variants'] = data['variants'].order_by('diameter_mm', 'pressure_bar')
            data['variant_json'] = [{'id': v.pk, 'product': v.product_id, 'd': str(v.diameter_mm), 'p': _str(v.pressure_bar), 'sdr': _str(v.sdr), 'wall': _str(v.wall_mm), 'weight': _str(v.weight_kg_m)} for v in data['variants']]
            strings = STRINGS[lang]
            site = SiteSettings.objects.first() or SiteSettings()
            data['picker_labels'] = {'mm': strings['unit_mm'], 'bar': strings['unit_bar'], 'kgm': strings['unit_kgm'], 'waMsg': strings['wa_quote_msg'], 'sep': '، ' if lang == 'ar' else ', ',
                                     'product': (obj.title_en or obj.title_ar) if lang == 'en' else obj.title_ar,
                                     'wa': re.sub(r'\D', '', site.whatsapp or site.phone or ''), 'contact': f'/{lang}/contact/'}
    if page == 'products':
        query = request.GET.get('q', '').strip()[:150]
        if query:
            data['products'] = data['products'].filter(Q(title_ar__icontains=query) | Q(title_en__icontains=query) | Q(description_ar__icontains=query) | Q(description_en__icontains=query))
        category = request.GET.get('category', '')
        if category:
            try:
                category_lookup = id_or_slug(category, 'category_id', 'category__slug')
            except ValueError:
                return JsonResponse({'error': 'Invalid category ID or slug'}, status=400)
            data['products'] = data['products'].filter(**category_lookup)
        data.update({'q': query, 'selected_category': category})
    if page in ('products', 'news', 'projects'):
        data['page_obj'] = Paginator(data[page], 12).get_page(request.GET.get('page'))
        data[page] = data['page_obj']
    if page == 'contact' and request.method == 'POST':
        form = EnquiryForm(request.POST, lang=lang)
        data['form'] = form
        if not allow_submission(request):
            form.add_error(None, 'Too many requests. Please try again in an hour.' if lang == 'en' else 'طلبات كثيرة. يرجى المحاولة بعد ساعة.')
            return render(request, 'site/contact.html', data, status=429)
        if form.is_valid():
            if not form.cleaned_data['website']:
                form.save()
            messages.success(request, 'تم إرسال طلبك بنجاح.' if lang == 'ar' else 'Your enquiry was sent successfully.')
            return redirect(f'/{lang}/contact/?success=1')
    elif request.method != 'GET':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'] if page == 'contact' else ['GET'])
    return render(request, f'site/{page}.html', data)

def variants(request, lang):
    if lang not in ('ar', 'en'):
        raise Http404
    if request.method != 'GET':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET'])
    from .models import ProductVariant
    qs = ProductVariant.objects.filter(approved=True, product__is_published=True).select_related('product')
    product = request.GET.get('product')
    if product:
        try:
            product_lookup = id_or_slug(product, 'product_id', 'product__slug')
        except ValueError:
            return JsonResponse({'error': 'Invalid product ID or slug'}, status=400)
        qs = qs.filter(**product_lookup)
    for field in ('diameter_mm', 'pressure_bar', 'sdr'):
        if request.GET.get(field):
            try:
                value = Decimal(request.GET[field])
                if not value.is_finite() or value <= 0 or value > Decimal('9999999'):
                    raise ValueError
                qs = qs.filter(**{field: value})
            except (InvalidOperation, ValueError):
                return JsonResponse({'error': f'Invalid {field}'}, status=400)
    rows = [{'id': v.pk, 'product_id': v.product_id, 'product': v.product.title_ar if lang == 'ar' else v.product.title_en or v.product.title_ar,
             **{f: str(getattr(v, f)) if getattr(v, f) is not None else None for f in ('diameter_mm', 'pressure_bar', 'sdr', 'wall_mm', 'weight_kg_m', 'length_m')}} for v in qs[:500]]
    return JsonResponse({'results': rows})
