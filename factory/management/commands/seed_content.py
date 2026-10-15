from datetime import date
from pathlib import Path
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from factory.catalogue import straight_pipe_rows
from factory.models import SiteSettings, Category, Product, ProductVariant, Certificate, Branch, Project, Resource

class Command(BaseCommand):
    help = 'Seed conservative reference content without replacing editorial changes or inventing measurements.'
    def add_arguments(self, parser):
        parser.add_argument('--reference-dir', type=Path, default=settings.BASE_DIR / 'reference')
    @transaction.atomic
    def handle(self, *args, **options):
        SiteSettings.objects.get_or_create(pk=1, defaults={
            'tagline_ar': 'أنابيب تُوصل الماء إلى كل مزرعة وكل بيت',
            'tagline_en': 'Pipes that bring water to every farm and every home',
            'about_ar': 'مصنع الدافنية للأنابيب في ليبيا، لإنتاج أنابيب البولي إيثيلين عالي الكثافة لمشاريع البنية التحتية والزراعة.',
            'about_en': 'Adafnia Pipe Factory in Libya produces high density polyethylene pipes for infrastructure and agriculture.',
            'phone': '+218 91 324 1428', 'whatsapp': '+218913241428',
            'address_ar': 'طريق مشروع المراعي، على بعد كيلومتر من الطريق السريع، الدافنية، مصراتة، ليبيا',
            'address_en': 'Pastures Project Road, 1 km from the highway, Adafnia, Misurata, Libya',
        })
        certificate_path = options['reference_dir'] / 'شهادات الدافنية .pdf'
        Branch.objects.get_or_create(title_ar='مصنع الدافنية', defaults={
            'is_factory': True,
            'title_en': 'Adafnia Factory',
            'address_ar': 'طريق مشروع المراعي، على بعد كيلومتر من الطريق السريع، الدافنية، مصراتة، ليبيا',
            'address_en': 'Pastures Project Road, 1 km from the highway, Adafnia, Misurata, Libya',
            'phone': '',
        })
        # Mark only the known legacy seed record; preserve its editorial fields.
        Branch.objects.filter(title_ar='مصنع الدافنية', title_en='Adafnia Factory', is_factory=False).update(is_factory=True)
        for title_ar, title_en, address_ar, address_en, phones in [
            ('مركز مبيعات طرابلس 1', 'Tripoli sales centre 1', 'طريق الدعوة الإسلامية، طرابلس', 'Islamic Call Road, Tripoli', ['091-3241428', '091-3591021']),
            ('مركز مبيعات طرابلس 2', 'Tripoli sales centre 2', 'طريق السواني، طرابلس', 'Al-Swani Road, Tripoli', ['092-6160178', '091-8070400', '091-6602222']),
            ('مركز مبيعات مصراتة 1', 'Misurata sales centre 1', 'الطريق الدائري الرابع، مصراتة', 'Fourth Ring Road, Misurata', ['091-3241640', '091-1130033']),
            ('مركز مبيعات مصراتة 2', 'Misurata sales centre 2', 'طريق المجمدات، مصراتة', 'Al-Mujammidat Road, Misurata', ['091-3865500', '091-3864400']),
        ]:
            Branch.objects.get_or_create(title_ar=title_ar, defaults={'title_en': title_en, 'address_ar': address_ar, 'address_en': address_en, 'phone': phones[0], 'description_ar': ' / '.join(phones), 'description_en': ' / '.join(phones)})
        for standard, suffix, ar, en in [
            ('ISO 9001:2015', 'QM', 'نظام إدارة الجودة', 'Quality Management System'),
            ('ISO 14001:2015', 'EM', 'نظام الإدارة البيئية', 'Environmental Management System'),
            ('ISO 45001:2018', 'OHS', 'نظام إدارة الصحة والسلامة المهنية', 'Occupational Health and Safety Management System'),
        ]:
            certificate, created = Certificate.objects.get_or_create(title_ar=standard, defaults={
                'title_en': standard,
                'description_ar': f'{ar}. رقم الشهادة 23.03.530-{suffix}. نسخة أرشيفية صادرة في 11 مايو 2023 وتنتهي في 10 مايو 2026.',
                'description_en': f'{en}. Certificate 23.03.530-{suffix}. Archival copy issued 11 May 2023; expired 10 May 2026.',
                'expires_on': date(2026, 5, 10), 'is_active': False,
            })
            if not certificate.file and certificate_path.is_file():
                with certificate_path.open('rb') as source:
                    certificate.file = File(source, name='certificates-2023.pdf')
                    certificate.full_clean()
                    certificate.save()
        for slug, ar, en, description_ar, description_en in [
            ('pe100-straight-pipes', 'أنابيب PE100 مستقيمة', 'PE100 straight pipes', 'أنابيب بولي إيثيلين عالية الكثافة لمشاريع المياه والري والبنية التحتية، تُورّد بأطوال مستقيمة.', 'High-density polyethylene pipes for water, irrigation and infrastructure, supplied in straight lengths.'),
            ('pe100-coils', 'لفّات أنابيب PE100', 'PE100 coils', 'لفّات بولي إيثيلين للري وشبكات المياه، بمقاسات وفئات ضغط متعددة حسب متطلبات المشروع.', 'Polyethylene coils for irrigation and water networks, in a range of diameters and pressure classes for your project.'),
        ]:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={'title_ar': ar, 'title_en': en, 'description_ar': description_ar, 'description_en': description_en})
            product, _ = Product.objects.get_or_create(slug=slug, defaults={'category': category, 'title_ar': ar, 'title_en': en, 'description_ar': description_ar, 'description_en': description_en, 'material': 'PE100', 'is_published': True})
            image = settings.BASE_DIR / 'static' / 'img' / ('coils.webp' if slug == 'pe100-coils' else 'pipes.webp')
            if not product.image and image.is_file():
                with image.open('rb') as source:
                    product.image = File(source, name=image.name)
                    product.full_clean()
                    product.save()
        for slug, ar, en, location_ar, location_en in [
            ('ouagadougou-conference-hall', 'قاعة مؤتمرات واغادوغو', 'Ouagadougou Conference Hall', 'سرت', 'Sirte'),
            ('abu-sitta-equestrian-grounds', 'ميدان أبو ستة للفروسية', 'Abu Sitta Equestrian Grounds', 'طرابلس', 'Tripoli'),
            ('al-afiya-agricultural-project', 'مشروع العافية الزراعي', 'Al-Afiya Agricultural Project', '', ''),
            ('talil-tourism-centre', 'مركز تليل السياحي', 'Talil Tourism Centre', 'صبراتة', 'Sabratha'),
        ]:
            Project.objects.get_or_create(slug=slug, defaults={'title_ar': ar, 'title_en': en, 'location_ar': location_ar, 'location_en': location_en, 'is_published': True})
        # Earlier seeds placed the Ouagadougou hall in Tripoli; it is in Sirte. Fix only that untouched value.
        Project.objects.filter(slug='ouagadougou-conference-hall', location_en='Tripoli', location_ar='طرابلس').update(location_ar='سرت', location_en='Sirte')
        # Catalogue sizes go in as drafts (approved=False) for engineer sign-off; never touch existing rows.
        straight = Product.objects.filter(slug='pe100-straight-pipes').first()
        if straight and not straight.variants.exists():
            ProductVariant.objects.bulk_create(ProductVariant(product=straight, approved=False, **row) for row in straight_pipe_rows())
        profile_path = options['reference_dir'] / 'ملف الدافنية A4.pdf'
        if profile_path.is_file():
            resource, _ = Resource.objects.get_or_create(title_ar='الملف التعريفي لمصنع الدافنية', defaults={'title_en': 'Adafnia company profile'})
            if not resource.file:
                with profile_path.open('rb') as source:
                    resource.file = File(source, name='adafnia-company-profile.pdf')
                    resource.full_clean()
                    resource.save()
        count = Certificate.objects.filter(expires_on__lt=timezone.localdate(), is_active=True).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'Content seeded. Archived {count} expired certificates. Catalogue sizes are added as unapproved drafts; no unverified certifications added.'))
