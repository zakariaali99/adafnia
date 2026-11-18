from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.http import HttpResponse
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.template import Template, Context
from PIL import Image
from .models import Category, Product, ProductVariant, NewsArticle, Project, Certificate, Enquiry, SiteSettings
from .validators import validate_pdf, validate_image

class BackendTests(TestCase):
    def test_profile_only_library_and_large_profile_upload(self):
        from .models import Resource
        self.assertFalse(Resource.objects.exists())
        self.client.force_login(self.staff)
        response = self.client.post('/dashboard/settings/new/', {
            'title_ar': 'الدافنية', 'title_en': 'Adafnia',
            'profile': SimpleUploadedFile('company-profile.pdf', b'%PDF-1.4\n' + b' ' * (26 * 1024 * 1024), content_type='application/pdf'),
        })
        self.assertEqual(response.status_code, 302)
        site = SiteSettings.objects.get(pk=1)
        self.assertGreater(site.profile.size, 10 * 1024 * 1024)
        self.client.logout()
        for lang in ('ar', 'en'):
            response = self.client.get(f'/{lang}/resources/')
            self.assertContains(response, site.profile.url)
            self.assertNotContains(response, 'Documents on request')
            self.assertFalse(response.context['resources'].exists())

    def test_public_branch_context_uses_structural_factory_flag(self):
        from .models import Branch
        factory = Branch.objects.create(title_ar='اسم مصنع معدل', title_en='Renamed factory', is_factory=True, address_en='Duplicate factory address')
        sales = Branch.objects.create(title_ar='مصنع الدافنية', title_en='Sales with factory-like name', address_en='Sales address')
        SiteSettings.objects.create(address_en='Canonical factory address', address_ar='عنوان المصنع الرسمي')
        for lang in ('ar', 'en'):
            response = self.client.get(f'/{lang}/contact/')
            self.assertEqual(list(response.context['branches']), [sales])
            self.assertNotIn(factory, response.context['branches'])
            self.assertNotContains(response, 'Duplicate factory address')
            self.assertContains(response, 'Canonical factory address' if lang == 'en' else 'عنوان المصنع الرسمي')

    def test_seed_marks_legacy_factory_without_overwriting_contact_fields(self):
        from .models import Branch
        factory = Branch.objects.create(title_ar='مصنع الدافنية', title_en='Adafnia Factory', address_ar='عنوان محرر', phone='edited-phone')
        call_command('seed_content', verbosity=0)
        factory.refresh_from_db()
        self.assertTrue(factory.is_factory)
        self.assertEqual(factory.address_ar, 'عنوان محرر')
        self.assertEqual(factory.phone, 'edited-phone')

    def test_edited_settings_and_branch_content_render_in_both_languages(self):
        from .models import Branch
        self.client.force_login(self.staff)
        response = self.client.post('/dashboard/settings/new/', {
            'title_ar': 'اسم الشركة المعدل', 'title_en': 'Edited company title',
            'tagline_ar': 'الشعار المعدل', 'tagline_en': 'Edited company tagline',
            'about_ar': 'نبذة الشركة المعدلة', 'about_en': 'Edited company introduction',
            'address_ar': 'عنوان المصنع المعدل', 'address_en': 'Edited factory address',
            'profile': SimpleUploadedFile('edited-profile.pdf', b'%PDF-1.4\n%%EOF', content_type='application/pdf'),
        })
        self.assertEqual(response.status_code, 302)
        site = SiteSettings.objects.get(pk=1)
        Branch.objects.create(title_ar='مبيعات', title_en='Sales', description_ar='أرقام المبيعات الإضافية 091-8070400', description_en='Additional sales numbers 091-8070400')
        self.client.logout()
        for lang in ('ar', 'en'):
            home = self.client.get(f'/{lang}/')
            self.assertContains(home, getattr(site, f'title_{lang}'))
            self.assertContains(home, getattr(site, f'tagline_{lang}'))
            self.assertContains(self.client.get(f'/{lang}/about/'), getattr(site, f'about_{lang}'))
            self.assertContains(self.client.get(f'/{lang}/resources/'), site.profile.url)
            contact = self.client.get(f'/{lang}/contact/')
            self.assertContains(contact, getattr(site, f'address_{lang}'))
            self.assertContains(contact, 'أرقام المبيعات الإضافية \u2066091-8070400\u2069' if lang == 'ar' else 'Additional sales numbers 091-8070400')

    def test_homepage_blank_material_never_infers_product_grade(self):
        from html.parser import HTMLParser
        class ProductCardParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_card = False
                self.text = []
            def handle_starttag(self, tag, attrs):
                if tag == 'a' and 'product-feature' in dict(attrs).get('class', '').split():
                    self.in_card = True
            def handle_endtag(self, tag):
                if tag == 'a':
                    self.in_card = False
            def handle_data(self, value):
                if self.in_card:
                    self.text.append(value)
        self.product.material = ''
        self.product.save()
        for lang in ('ar', 'en'):
            parser = ProductCardParser()
            parser.feed(self.client.get(f'/{lang}/').content.decode())
            text = ' '.join(parser.text)
            self.assertIn(self.product.title_ar if lang == 'ar' else self.product.title_en, text)
            self.assertNotIn('PE100', text)

    def test_adversarial_identifiers_are_controlled(self):
        malformed = ['²', '9' * 5000, '١', '１', '𝟚', '0', '-1', '9223372036854775808']
        for value in malformed:
            for lang in ('ar', 'en'):
                for path, field in [('products/', 'category'), ('contact/', 'product'), ('contact/', 'variant'), ('api/variants/', 'product')]:
                    with self.subTest(lang=lang, path=path, field=field, value=value[:30]):
                        self.assertEqual(self.client.get(f'/{lang}/{path}', {field: value}).status_code, 400)
                for section in ('products', 'news', 'projects'):
                    self.assertEqual(self.client.get(f'/{lang}/{section}/{value}/').status_code, 404)
        for path in ('', 'products/', 'contact/', 'api/variants/', f'products/{self.product.pk}/'):
            self.assertEqual(self.client.get(f'/fr/{path}', {'product': '²'}).status_code, 404)

    def test_shared_id_parser_boundaries(self):
        from .identifiers import parse_id, id_or_slug, MAX_ID
        self.assertEqual(parse_id(str(MAX_ID)), MAX_ID)
        self.assertEqual(parse_id('001'), 1)
        self.assertEqual(id_or_slug('water'), {'slug': 'water'})
        for value in ['²', '١', '１', '9' * 5000, '0', str(MAX_ID + 1), '', ' 1', '+1']:
            with self.subTest(value=value[:30]), self.assertRaises(ValueError):
                parse_id(value)
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_dir = TemporaryDirectory()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_dir.name)
        cls.media_override.enable()
    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        cls.media_dir.cleanup()
        super().tearDownClass()
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(title_ar='أنابيب', title_en='Pipes', slug='pipes')
        cls.product = Product.objects.create(title_ar='مياه', title_en='Water', slug='water', category=cls.category, is_published=True)
        cls.draft = Product.objects.create(title_ar='مسودة', slug='draft', category=cls.category)
        cls.variant = ProductVariant.objects.create(product=cls.product, diameter_mm=100, approved=True)
        ProductVariant.objects.create(product=cls.product, diameter_mm=200)
        ProductVariant.objects.create(product=cls.draft, diameter_mm=300, approved=True)
        cls.staff = get_user_model().objects.create_user('editor', password='test-only-strong-123', is_staff=True)
        cls.user = get_user_model().objects.create_user('reader', password='test-only-strong-123')

    def test_variant_api_visibility_and_validation(self):
        response = self.client.get('/en/api/variants/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([v['id'] for v in response.json()['results']], [self.variant.pk])
        self.assertEqual(self.client.post('/ar/api/variants/').status_code, 405)
        for value in ['NaN', 'bad', '-1', 'Infinity']:
            self.assertEqual(self.client.get('/ar/api/variants/', {'diameter_mm': value}).status_code, 400)
        self.assertEqual(self.client.get('/fr/api/variants/').status_code, 404)
        self.assertEqual(self.client.get('/ar/api/variants/', {'product': 'draft'}).json()['results'], [])

    def test_drafts_and_future_news_are_hidden(self):
        NewsArticle.objects.create(title_ar='future', slug='future', status='published', published_at=timezone.now()+timedelta(days=1))
        NewsArticle.objects.create(title_ar='draft', slug='draft')
        Project.objects.create(title_ar='draft', slug='draft')
        for path in ['/ar/products/draft/', '/ar/news/future/', '/en/news/draft/', '/en/projects/draft/']:
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_context_contract_and_approved_related_variants(self):
        from .context import site_context
        def capture(request, template, data, **kwargs):
            self.assertEqual(template, 'site/product_detail.html')
            self.assertEqual(list(data['product'].variants.all()), [self.variant])
            context = site_context(request)
            self.assertEqual(context['lang'], 'en')
            self.assertEqual(context['current_path'], 'products/water/')
            return HttpResponse('ok')
        with patch('factory.views.render', side_effect=capture):
            self.assertEqual(self.client.get('/en/products/water/').status_code, 200)

    def test_certificate_expiry(self):
        from .views import public_data
        expired = Certificate.objects.create(title_ar='old', expires_on=timezone.localdate()-timedelta(days=1))
        current = Certificate.objects.create(title_ar='today', expires_on=timezone.localdate())
        self.assertEqual(expired.status, 'expired')
        self.assertIn(current, public_data()['certificates'])
        self.assertNotIn(expired, public_data()['certificates'])
        self.assertIn(expired, public_data()['archived_certificates'])

    def test_staff_authorization_all_crud(self):
        self.assertEqual(self.client.get('/dashboard/').status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/dashboard/').status_code, 403)
        self.client.force_login(self.staff)
        from .dashboard import REGISTRY
        self.assertEqual(self.client.get('/dashboard/').status_code, 200)
        for section in REGISTRY:
            self.assertEqual(self.client.get(f'/dashboard/{section}/').status_code, 200)
            # Enquiries come only from the public form; staff read them, they do not create them.
            self.assertEqual(self.client.get(f'/dashboard/{section}/new/').status_code, 302 if section == 'enquiries' else 200)

    def test_dashboard_bulk_approve_variants(self):
        pending = ProductVariant.objects.create(product=self.product, diameter_mm=63, pressure_bar=10)
        other = ProductVariant.objects.create(product=self.product, diameter_mm=75, pressure_bar=10)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/dashboard/variants/approve/', {'ids': [pending.pk]}).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/dashboard/variants/approve/').status_code, 405)
        self.assertContains(self.client.get('/dashboard/variants/?state=pending'), 'بانتظار الاعتماد')
        response = self.client.post('/dashboard/variants/approve/', {'ids': [pending.pk, 'x'], 'next': 'https://evil.example/'})
        self.assertRedirects(response, '/dashboard/variants/', fetch_redirect_response=False)
        pending.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(pending.approved)
        self.assertFalse(other.approved)

    def test_dashboard_save_errors_delete_protection(self):
        self.client.force_login(self.staff)
        response = self.client.post('/dashboard/categories/new/', {'title_ar': 'جديد', 'slug': 'new'})
        self.assertEqual(response.status_code, 302)
        response = self.client.post('/dashboard/categories/new/', {'slug': 'bad'})
        self.assertContains(response, 'errorlist')
        self.client.get(f'/dashboard/categories/{self.category.pk}/delete/')
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        self.assertContains(self.client.post(f'/dashboard/categories/{self.category.pk}/delete/'), 'لا يمكن حذف')

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        self.assertEqual(client.post('/dashboard/categories/new/', {}).status_code, 403)
        self.assertEqual(client.post('/ar/contact/', {}).status_code, 403)

    def test_contact_success_honeypot_draft_and_limit(self):
        payload = {'name': 'عميل', 'phone': '+218913241428', 'subject': 'طلب', 'message': 'تفاصيل الطلب'}
        self.assertEqual(self.client.post('/ar/contact/', payload).status_code, 302)
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual(self.client.post('/en/contact/', {**payload, 'website': 'spam'}).status_code, 302)
        self.assertEqual(Enquiry.objects.count(), 1)
        with patch('factory.views.render', return_value=HttpResponse('invalid')) as render:
            self.client.post('/ar/contact/', {**payload, 'product': self.draft.pk})
            self.assertIn('product', render.call_args.args[2]['form'].errors)
        for _ in range(2):
            self.client.post('/ar/contact/', payload)
        with patch('factory.views.render', return_value=HttpResponse(status=429)):
            self.assertEqual(self.client.post('/ar/contact/', payload).status_code, 429)

    def test_upload_validation(self):
        for name, content in [('evil.pdf', b'<script>bad</script>'), ('bad.svg', b'%PDF-1.4')]:
            with self.assertRaises(ValidationError):
                validate_pdf(SimpleUploadedFile(name, content))
        validate_pdf(SimpleUploadedFile('valid.pdf', b'%PDF-1.4\n%%EOF'))
        with self.assertRaises(ValidationError):
            validate_image(SimpleUploadedFile('bad.png', b'not an image'))
        buffer = BytesIO()
        Image.new('RGB', (2, 2)).save(buffer, format='PNG')
        validate_image(SimpleUploadedFile('good.png', buffer.getvalue()))
        with self.assertRaises(ValidationError):
            validate_pdf(SimpleUploadedFile('large.pdf', b'%PDF-' + b'x'*(10*1024*1024)))

    def test_seed_idempotent_preserves_edits(self):
        call_command('seed_content', verbosity=0)
        counts = (Category.objects.count(), Product.objects.count())
        site = SiteSettings.objects.get(pk=1)
        site.phone = 'edited'
        site.save()
        call_command('seed_content', verbosity=0)
        self.assertEqual(counts, (Category.objects.count(), Product.objects.count()))
        self.assertEqual(SiteSettings.objects.get(pk=1).phone, 'edited')

    def test_translation_fallback(self):
        output = Template("{% load site_tags %}{% translated obj 'title' 'en' %}|{{ obj|field:'description'|tr:'ar' }}").render(Context({'obj': self.category}))
        self.assertEqual(output, 'Pipes|')

    def test_all_bilingual_route_contexts(self):
        with patch('factory.views.render', return_value=HttpResponse('ok')) as render:
            for lang in ('ar', 'en'):
                for page in ('', 'about/', 'products/', 'news/', 'projects/', 'quality/', 'resources/', 'contact/'):
                    self.assertEqual(self.client.get(f'/{lang}/{page}').status_code, 200)
                    self.assertIn('form', render.call_args.args[2])
        self.assertEqual(self.client.get('/fr/').status_code, 404)

    def test_seed_archives_reference_certificates(self):
        call_command('seed_content', verbosity=0)
        self.assertEqual(Certificate.objects.filter(expires_on='2026-05-10', is_active=False).count(), 3)

    def test_public_templates_render_both_languages_and_pk_details(self):
        article = NewsArticle.objects.create(title_ar='خبر', title_en='Factory news', slug='live-news', status='published')
        project = Project.objects.create(title_ar='مشروع', title_en='Project', slug='live-project', is_published=True)
        for lang in ('ar', 'en'):
            for path in ('', 'about/', 'products/', 'news/', 'projects/', 'quality/', 'resources/', 'contact/', f'products/{self.product.pk}/', f'news/{article.pk}/', f'projects/{project.pk}/', 'products/water/'):
                response = self.client.get(f'/{lang}/{path}')
                self.assertEqual(response.status_code, 200, f'/{lang}/{path}')
                self.assertNotContains(response, 'href="/en//')
                self.assertNotContains(response, 'href="/ar//')
        self.assertEqual(self.client.get(f'/ar/products/{self.draft.pk}/').status_code, 404)

    def test_pk_filters_selectors_quote_and_localized_errors(self):
        response = self.client.get('/en/products/', {'category': self.category.pk})
        self.assertContains(response, 'Water')
        detail = self.client.get(f'/en/products/{self.product.pk}/')
        self.assertEqual(list(detail.context['diameters']), [self.variant.diameter_mm])
        quote = self.client.get('/en/contact/', {'product': self.product.pk, 'variant': self.variant.pk})
        self.assertContains(quote, 'Diameter (mm): 100<')
        self.assertContains(quote, '>Name')
        self.assertContains(quote, '>Water</option>')
        private = ProductVariant.objects.get(product=self.product, approved=False)
        quote = self.client.get('/en/contact/', {'variant': private.pk})
        self.assertFalse(quote.context['form'].initial.get('message'))
        invalid = self.client.post('/en/contact/', {'name': '', 'phone': 'x', 'subject': '', 'message': ''})
        self.assertContains(invalid, 'This field is required.')
        self.assertContains(invalid, 'Enter a valid phone number.')

    def test_dashboard_auto_slug_hidden(self):
        self.client.force_login(self.staff)
        self.assertNotContains(self.client.get('/dashboard/products/new/'), 'name="slug"')
        for _ in range(2):
            response = self.client.post('/dashboard/categories/new/', {'title_ar': 'عنوان', 'title_en': 'Automatic title'})
            self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(slug='automatic-title').exists())
        self.assertTrue(Category.objects.filter(slug='automatic-title-2').exists())

    def test_seed_supplied_files_and_reference_projects(self):
        from pathlib import Path
        from .models import Resource, Branch
        reference = Path('/Users/zakaria/projects/Claude/adafnia/reference')
        if not reference.is_dir():
            self.skipTest('Supplied reference directory is not present on this host')
        call_command('seed_content', reference_dir=reference, verbosity=0)
        resource = Resource.objects.get(title_en='Adafnia company profile')
        self.assertTrue(resource.file.storage.exists(resource.file.name))
        self.assertEqual(Certificate.objects.exclude(file='').count(), 3)
        self.assertEqual(Project.objects.filter(year__isnull=True, is_published=True).count(), 4)
        self.assertEqual(Branch.objects.exclude(title_ar='مصنع الدافنية').count(), 4)
        self.assertEqual(Branch.objects.get(title_ar='مصنع الدافنية').phone, '')
        self.assertEqual(set(Product.objects.filter(is_published=True).exclude(pk=self.product.pk).values_list('title_en', flat=True)), {'PE100 straight pipes', 'PE100 coils'})
        for product in Product.objects.filter(material='PE100'):
            self.assertTrue(product.image.storage.exists(product.image.name))
        for lang in ('ar', 'en'):
            for path in ('', 'products/', 'projects/', 'quality/', 'resources/', 'contact/'):
                self.assertEqual(self.client.get(f'/{lang}/{path}').status_code, 200)
            for product in Product.objects.filter(is_published=True):
                response = self.client.get(f'/{lang}/products/{product.pk}/')
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'site/product_detail.html')
            for project in Project.objects.filter(is_published=True):
                response = self.client.get(f'/{lang}/projects/{project.pk}/')
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'site/project_detail.html')

    def test_login_rate_limit_recovers_and_is_separate_from_contact(self):
        from .models import SubmissionThrottle
        for _ in range(10):
            self.assertEqual(self.client.post('/dashboard/login/', {'username': 'missing', 'password': 'invalid'}).status_code, 200)
        self.assertEqual(self.client.post('/dashboard/login/', {'username': 'editor', 'password': 'test-only-strong-123'}).status_code, 429)
        self.assertEqual(self.client.post('/en/contact/', {'name': 'Test', 'phone': '1234567', 'subject': 'Test', 'message': 'Message'}).status_code, 302)
        SubmissionThrottle.objects.update(started_at=timezone.now()-timedelta(minutes=16))
        self.assertEqual(self.client.post('/dashboard/login/', {'username': 'editor', 'password': 'test-only-strong-123'}).status_code, 302)

    def test_dashboard_image_optimization_labels_and_expiry_warning(self):
        self.client.force_login(self.staff)
        form = self.client.get('/dashboard/products/new/').context['form']
        self.assertEqual(form.fields['title_en'].label, 'العنوان بالإنجليزية')
        buffer = BytesIO()
        Image.new('RGB', (2400, 1200), 'blue').save(buffer, format='PNG')
        original_bytes = buffer.getvalue()
        response = self.client.post(f'/dashboard/products/{self.product.pk}/edit/', {'title_ar': 'مياه', 'title_en': 'Water', 'category': self.category.pk, 'is_published': 'on', 'image': SimpleUploadedFile('source.png', original_bytes, content_type='image/png')})
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertTrue(self.product.image.name.endswith('.webp'))
        with Image.open(self.product.image.path) as image:
            self.assertEqual(image.size, (1920, 960))
            self.assertEqual(image.format, 'WEBP')
        self.assertEqual(buffer.getvalue(), original_bytes)
        Certificate.objects.create(title_ar='قريب الانتهاء', expires_on=timezone.localdate()+timedelta(days=30))
        Certificate.objects.create(title_ar='بعيد الانتهاء', expires_on=timezone.localdate()+timedelta(days=31))
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'قريب الانتهاء')
        self.assertNotContains(response, 'بعيد الانتهاء')

    def test_seed_preserves_existing_product_and_branch_edits(self):
        from .models import Branch
        legacy = Product.objects.create(category=self.category, slug='drip-irrigation', title_ar='معدل', title_en='Drip irrigation pipes', is_published=True)
        branch = Branch.objects.create(title_ar='مصنع الدافنية', phone='+218 91 324 1428')
        call_command('seed_content', verbosity=0)
        legacy.refresh_from_db()
        branch.refresh_from_db()
        self.assertTrue(legacy.is_published)
        self.assertEqual(branch.phone, '+218 91 324 1428')

    def test_robots_and_sitemap_only_visible_pk_routes(self):
        from xml.etree.ElementTree import fromstring
        article = NewsArticle.objects.create(title_ar='منشور', slug='visible', status='published')
        draft = NewsArticle.objects.create(title_ar='مسودة', slug='private')
        future = NewsArticle.objects.create(title_ar='مستقبل', slug='future', status='published', published_at=timezone.now()+timedelta(days=1))
        project = Project.objects.create(title_ar='منشور', slug='visible', is_published=True)
        response = self.client.get('/sitemap.xml', HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        root = fromstring(response.content)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locations = [element.text for element in root.findall('s:url/s:loc', ns)]
        self.assertEqual(len(locations), 22)
        for lang in ('ar', 'en'):
            self.assertIn(f'http://localhost/{lang}/products/{self.product.pk}/', locations)
            self.assertIn(f'http://localhost/{lang}/news/{article.pk}/', locations)
            self.assertIn(f'http://localhost/{lang}/projects/{project.pk}/', locations)
            self.assertNotIn(f'http://localhost/{lang}/products/{self.draft.pk}/', locations)
            for hidden in (draft, future):
                self.assertNotIn(f'http://localhost/{lang}/news/{hidden.pk}/', locations)
        self.assertContains(response, article.published_at.date().isoformat())
        robots = self.client.get('/robots.txt', HTTP_HOST='localhost')
        self.assertContains(robots, 'Sitemap: http://localhost/sitemap.xml')
        self.assertContains(robots, 'Disallow: /dashboard/')

    def test_copy_says_international_not_german_standards(self):
        from factory.strings import STRINGS
        for lang, table in STRINGS.items():
            for key, value in table.items():
                self.assertNotRegex(str(value), r'ألمان|الماني|German', f'{lang}.{key}')
        self.assertIn('العالمية', STRINGS['ar']['lab_text'])
        self.assertIn('international', STRINGS['en']['lab_text'])

    @override_settings(DEBUG=False)
    def test_branded_404_follows_language(self):
        ar = self.client.get('/ar/products/no-such-pipe/')
        self.assertEqual(ar.status_code, 404)
        self.assertContains(ar, 'الصفحة غير موجودة', status_code=404)
        en = self.client.get('/en/nothing/here/')
        self.assertContains(en, 'Page not found', status_code=404)
        self.assertContains(en, 'href="/en/products/"', status_code=404)

    def test_arabic_count_agreement(self):
        from factory.dashboard import ar_count, SIZES
        self.assertEqual(ar_count(1, *SIZES), 'مقاس واحد')
        self.assertEqual(ar_count(2, *SIZES), 'مقاسان')
        self.assertEqual(ar_count(5, *SIZES), '5 مقاسات')
        self.assertEqual(ar_count(81, *SIZES), '81 مقاساً')
        self.assertEqual(ar_count(111, *SIZES), '111 مقاساً')

    def test_deleted_and_replaced_files_are_removed(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            from .models import Resource
            from django.core.files.base import ContentFile
            pdf = b'%PDF-1.4\n%%EOF'
            with self.captureOnCommitCallbacks(execute=True):
                resource = Resource.objects.create(title_ar='ملف', file=ContentFile(pdf, name='a.pdf'))
            first = resource.file.name
            storage = resource.file.storage
            self.assertTrue(storage.exists(first))
            with self.captureOnCommitCallbacks(execute=True):
                resource.file = ContentFile(pdf, name='b.pdf')
                resource.save()
            self.assertFalse(storage.exists(first))
            second = resource.file.name
            with self.captureOnCommitCallbacks(execute=True):
                resource.save()
            self.assertTrue(storage.exists(second))
            with self.captureOnCommitCallbacks(execute=True):
                resource.delete()
            self.assertFalse(storage.exists(second))

    def test_enquiry_is_read_only_with_contact_actions(self):
        from factory.dashboard import wa_number
        self.assertEqual(wa_number('091-3241428'), '218913241428')
        self.assertEqual(wa_number('+218 91 324 1428'), '218913241428')
        self.assertEqual(wa_number('00218913241428'), '218913241428')
        staff = get_user_model().objects.create_user('desk', password='x-Strong-pass-123', is_staff=True)
        self.client.force_login(staff)
        enquiry = Enquiry.objects.create(name='سالم', phone='092-6160178', email='s@example.com', subject='عرض سعر', message='أحتاج 110 مم\nضغط 16')
        page = self.client.get(f'/dashboard/enquiries/{enquiry.pk}/edit/')
        self.assertContains(page, 'href="tel:092-6160178"'.replace('-', ''))
        self.assertContains(page, 'https://wa.me/218926160178?text=')
        self.assertContains(page, 'mailto:s@example.com')
        self.assertContains(page, 'أحتاج 110 مم<br>ضغط 16')
        self.assertNotContains(page, '<textarea')
        self.assertEqual(self.client.post(f'/dashboard/enquiries/{enquiry.pk}/edit/', {'name': 'x'}).status_code, 405)
        self.assertRedirects(self.client.get('/dashboard/enquiries/new/'), '/dashboard/enquiries/')

    def test_arabic_text_isolates_latin_number_runs(self):
        from factory.templatetags.site_tags import isolate_ltr
        self.assertEqual(isolate_ltr('رقم الشهادة 23.03.530-QM.'), 'رقم الشهادة ⁦23.03.530-QM⁩.')
        self.assertEqual(isolate_ltr('حتى 2026-05-10'), 'حتى ⁦2026-05-10⁩')
        self.assertEqual(isolate_ltr('منذ 2006 في مصراتة'), 'منذ 2006 في مصراتة')
        self.assertEqual(isolate_ltr('Certificate 23.03.530-QM'), 'Certificate 23.03.530-QM')
