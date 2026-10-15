from functools import wraps
from django import forms
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q, ProtectedError
from django.http import Http404, HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import redirect_to_login
from django.utils.text import slugify
from uuid import uuid4
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image, ImageOps
from .views import allow_submission
from . import models

REGISTRY = {
    'categories': (models.Category, 'التصنيفات'), 'products': (models.Product, 'المنتجات'),
    'variants': (models.ProductVariant, 'المقاسات'), 'news': (models.NewsArticle, 'الأخبار والجدولة'),
    'projects': (models.Project, 'المشاريع'), 'certificates': (models.Certificate, 'الشهادات والصلاحية'),
    'resources': (models.Resource, 'الملفات الفنية'), 'branches': (models.Branch, 'الفروع'),
    'enquiries': (models.Enquiry, 'طلبات العملاء'), 'settings': (models.SiteSettings, 'إعدادات الموقع'),
}

def staff_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_active or not request.user.is_staff:
            return HttpResponseForbidden('هذه الصفحة مخصصة لإدارة الموقع.')
        return view(request, *args, **kwargs)
    return wrapped

class DashboardLogin(LoginView):
    template_name = 'dashboard/login.html'
    def post(self, request, *args, **kwargs):
        if not allow_submission(request, namespace='dashboard-login', limit=10, window=900):
            form = self.get_form()
            form.add_error(None, 'محاولات دخول كثيرة. يرجى المحاولة بعد 15 دقيقة.')
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)
    def form_valid(self, form):
        if not form.get_user().is_staff:
            form.add_error(None, 'هذا الحساب غير مخوّل بالدخول إلى لوحة الإدارة.')
            return self.form_invalid(form)
        return super().form_valid(form)

# Per-section presentation: nav icon, the "add" button label (None = no add button) and the nav group.
META = {
    'products': ('box', 'منتج جديد', 'content'), 'categories': ('folder', 'عائلة جديدة', 'content'),
    'variants': ('ruler', 'مقاس جديد', 'content'), 'news': ('news', 'خبر جديد', 'content'),
    'projects': ('flag', 'مشروع جديد', 'content'), 'certificates': ('award', 'شهادة جديدة', 'content'),
    'resources': ('doc', 'ملف جديد', 'content'), 'branches': ('pin', 'مركز بيع جديد', 'content'),
    'enquiries': ('inbox', None, 'inbox'), 'settings': ('gear', None, 'site'),
}
NAV_ORDER = ['enquiries', 'products', 'variants', 'categories', 'news', 'projects', 'certificates', 'resources', 'branches', 'settings']

def context():
    return {'sections': [(key, REGISTRY[key][1], META[key][0]) for key in NAV_ORDER]}

def section_context(section):
    icon, add_label, _ = META[section]
    return {**context(), 'section': section, 'label': REGISTRY[section][1], 'icon': icon, 'add_label': add_label}

FIELD_LABELS = {
    'is_factory': 'سجل المصنع (العنوان من إعدادات الموقع)',
    'title_ar': 'العنوان بالعربية', 'title_en': 'العنوان بالإنجليزية',
    'description_ar': 'الوصف بالعربية', 'description_en': 'الوصف بالإنجليزية',
    'body_ar': 'النص بالعربية', 'body_en': 'النص بالإنجليزية',
    'category': 'عائلة المنتج', 'material': 'المادة الخام', 'image': 'الصورة',
    'is_published': 'منشور للزوار', 'product': 'المنتج', 'approved': 'معتمد للنشر',
    'diameter_mm': 'القطر (مم)', 'pressure_bar': 'الضغط (بار)', 'sdr': 'نسبة الأبعاد SDR',
    'wall_mm': 'سماكة الجدار (مم)', 'weight_kg_m': 'الوزن (كجم/م)', 'length_m': 'الطول (م)',
    'published_at': 'موعد النشر بتوقيت ليبيا', 'status': 'حالة النشر',
    'location_ar': 'الموقع بالعربية', 'location_en': 'الموقع بالإنجليزية', 'year': 'السنة',
    'file': 'ملف PDF', 'expires_on': 'تاريخ انتهاء الصلاحية', 'is_active': 'نشطة',
    'address_ar': 'العنوان البريدي بالعربية', 'address_en': 'العنوان البريدي بالإنجليزية',
    'phone': 'الهاتف', 'email': 'البريد الإلكتروني', 'whatsapp': 'رقم واتساب',
    'tagline_ar': 'الشعار النصي بالعربية', 'tagline_en': 'الشعار النصي بالإنجليزية',
    'about_ar': 'نبذة بالعربية', 'about_en': 'نبذة بالإنجليزية', 'profile': 'ملف الشركة PDF',
    'name': 'اسم العميل', 'subject': 'الموضوع', 'message': 'الرسالة',
}

WIDE_WIDGETS = {'checkbox', 'clearablefile', 'file'}

def form_rows(form):
    """Group a form into rows: Arabic/English twins sit side by side, files and switches take a full row."""
    rows, fields = [], list(form)
    i = 0
    while i < len(fields):
        field = fields[i]
        twin = fields[i + 1] if i + 1 < len(fields) else None
        if field.name.endswith('_ar') and twin is not None and twin.name == field.name[:-3] + '_en':
            rows.append(('pair', [field, twin]))
            i += 2
            continue
        rows.append(('wide' if field.widget_type in WIDE_WIDGETS or field.widget_type == 'textarea' else 'single', [field]))
        i += 1
    return rows

def optimize_image(instance, form):
    if 'image' not in form.changed_data or not form.cleaned_data.get('image'):
        return
    source = form.cleaned_data['image']
    source.seek(0)
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')
        output = BytesIO()
        image.save(output, format='WEBP', quality=82, method=6)
    instance.image = ContentFile(output.getvalue(), name=f'{uuid4().hex}.webp')

@staff_required
def index(request):
    today = timezone.localdate()
    expiring = models.Certificate.objects.filter(is_active=True, expires_on__gte=today, expires_on__lte=today + timedelta(days=30)).order_by('expires_on')
    expired = models.Certificate.objects.filter(is_active=True, expires_on__lt=today).order_by('expires_on')
    has_valid = models.Certificate.objects.filter(is_active=True).filter(Q(expires_on__gte=today) | Q(expires_on__isnull=True)).exists()
    counts = [(key, REGISTRY[key][1], META[key][0], REGISTRY[key][0].objects.count()) for key in NAV_ORDER if key not in ('settings', 'enquiries')]
    return render(request, 'dashboard/index.html', {**context(), 'expiring_certificates': expiring, 'expired_certificates': expired, 'no_valid_certificate': not has_valid, 'counts': counts,
        'pending_variants': models.ProductVariant.objects.filter(approved=False).count(),
        'draft_products': models.Product.objects.filter(is_published=False).count(),
        'recent_enquiries': models.Enquiry.objects.select_related('product')[:5],
        'week_enquiries': models.Enquiry.objects.filter(created_at__gte=timezone.now() - timedelta(days=7)).count()})

@staff_required
def listing(request, section):
    if section not in REGISTRY:
        raise Http404
    model, label = REGISTRY[section]
    qs = model.objects.all()
    q = request.GET.get('q', '').strip()[:150]
    fields = {field.name for field in model._meta.fields}
    if q:
        search = Q()
        for field in fields & {'title_ar', 'title_en', 'name', 'subject', 'phone', 'email'}:
            search |= Q(**{field + '__icontains': q})
        if section == 'variants':
            search |= Q(product__title_ar__icontains=q) | Q(product__title_en__icontains=q)
            try:
                search |= Q(diameter_mm=Decimal(q))
            except InvalidOperation:
                pass
        if search:
            qs = qs.filter(search)
    state = ''
    if section == 'variants':
        qs = qs.select_related('product').order_by('product__title_ar', 'diameter_mm', 'pressure_bar')
        state = request.GET.get('state', '')
        if state in ('pending', 'approved'):
            qs = qs.filter(approved=state == 'approved')
    elif section == 'products':
        qs = qs.select_related('category').order_by('-pk')
    elif section == 'enquiries':
        qs = qs.select_related('product').order_by('-created_at')
    else:
        qs = qs.order_by('-pk')
    per_page = 50 if section == 'variants' else 25
    return render(request, 'dashboard/list.html', {**section_context(section), 'q': q, 'state': state,
        'pending_count': model.objects.filter(approved=False).count() if section == 'variants' else 0,
        'page_obj': Paginator(qs, per_page).get_page(request.GET.get('page'))})

@staff_required
def approve_variants(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    ids = [int(value) for value in request.POST.getlist('ids') if value.isdigit()]
    updated = models.ProductVariant.objects.filter(pk__in=ids, approved=False).update(approved=True)
    messages.success(request, f'تم اعتماد {updated} مقاساً.' if updated else 'لم يتم تحديد مقاسات غير معتمدة.')
    return redirect(request.POST.get('next') if str(request.POST.get('next', '')).startswith('/dashboard/variants/') else '/dashboard/variants/')

@staff_required
def edit(request, section, pk=None):
    if section not in REGISTRY:
        raise Http404
    model, label = REGISTRY[section]
    obj = get_object_or_404(model, pk=pk) if pk else None
    if section == 'settings':
        obj = models.SiteSettings.objects.first() or models.SiteSettings(pk=1)
    Form = forms.modelform_factory(model, labels=FIELD_LABELS, exclude=['slug'] if any(field.name == 'slug' for field in model._meta.fields) else [], widgets={
        'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        'expires_on': forms.DateInput(attrs={'type': 'date'}),
    })
    form = Form(request.POST or None, request.FILES or None, instance=obj)
    form.label_suffix = ''
    for name, bound in form.fields.items():
        if name.endswith('_en') or name in ('phone', 'whatsapp', 'email', 'slug'):
            bound.widget.attrs.setdefault('dir', 'ltr')
        if isinstance(bound.widget, forms.Textarea):
            bound.widget.attrs['rows'] = 8 if name.startswith('body') else 4
    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        optimize_image(instance, form)
        if hasattr(instance, 'slug') and not instance.slug:
            base = slugify(instance.title_en)[:45] or f'{section}-{uuid4().hex[:10]}'
            candidate, suffix = base, 2
            while model.objects.filter(slug=candidate).exclude(pk=instance.pk).exists():
                candidate = f'{base}-{suffix}'
                suffix += 1
            instance.slug = candidate
        instance.save()
        form.save_m2m()
        messages.success(request, 'تم الحفظ بنجاح.')
        return redirect('dashboard-list', section=section)
    return render(request, 'dashboard/form.html', {**section_context(section), 'form': form, 'object': obj, 'rows': form_rows(form)})

@staff_required
def delete(request, section, pk):
    if section not in REGISTRY or section == 'settings':
        raise Http404
    model, label = REGISTRY[section]
    obj = get_object_or_404(model, pk=pk)
    error = ''
    if request.method == 'POST':
        try:
            obj.delete()
            messages.success(request, 'تم الحذف.')
            return redirect('dashboard-list', section=section)
        except ProtectedError:
            error = 'لا يمكن حذف تصنيف مرتبط بمنتجات. انقل المنتجات أولاً.'
    return render(request, 'dashboard/delete.html', {**section_context(section), 'object': obj, 'error': error})
