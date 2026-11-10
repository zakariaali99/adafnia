from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .validators import upload_path, validate_image, validate_pdf, validate_resource_pdf

class Content(models.Model):
    title_ar = models.CharField('العنوان بالعربية', max_length=250)
    title_en = models.CharField('العنوان بالإنجليزية', max_length=250, blank=True)
    description_ar = models.TextField('الوصف بالعربية', blank=True)
    description_en = models.TextField('الوصف بالإنجليزية', blank=True)
    class Meta:
        abstract = True
        ordering = ['pk']
    def __str__(self):
        return self.title_ar

class Category(Content):
    slug = models.SlugField(unique=True)

class Product(Content):
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    material = models.CharField('المادة', max_length=100, blank=True)
    image = models.ImageField(upload_to=upload_path, validators=[validate_image], blank=True)
    is_published = models.BooleanField('منشور', default=False)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    diameter_mm = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    pressure_bar = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])
    sdr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])
    wall_mm = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(0.001)])
    weight_kg_m = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, validators=[MinValueValidator(0.0001)])
    length_m = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])
    approved = models.BooleanField('معتمد للنشر', default=False)
    class Meta:
        ordering = ['diameter_mm', 'pk']
    def __str__(self):
        return f'{self.product} — {self.diameter_mm} mm'

class NewsArticle(Content):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'مسودة'
        PUBLISHED = 'published', 'منشور / مجدول'
    slug = models.SlugField(unique=True)
    body_ar = models.TextField(blank=True)
    body_en = models.TextField(blank=True)
    image = models.ImageField(upload_to=upload_path, validators=[validate_image], blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    class Meta:
        ordering = ['-published_at', '-pk']
    @property
    def is_scheduled(self):
        return self.status == 'published' and self.published_at > timezone.now()

class Project(Content):
    slug = models.SlugField(unique=True)
    body_ar = models.TextField(blank=True)
    body_en = models.TextField(blank=True)
    image = models.ImageField(upload_to=upload_path, validators=[validate_image], blank=True)
    location_ar = models.CharField(max_length=250, blank=True)
    location_en = models.CharField(max_length=250, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1900), MaxValueValidator(2200)])
    is_published = models.BooleanField(default=False)

class Certificate(Content):
    file = models.FileField(upload_to=upload_path, validators=[validate_pdf], blank=True)
    expires_on = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    @property
    def is_expired(self):
        return bool(self.expires_on and self.expires_on < timezone.localdate())
    @property
    def status(self):
        return 'expired' if self.is_expired else ('current' if self.is_active else 'archived')

class Resource(Content):
    file = models.FileField(upload_to=upload_path, validators=[validate_resource_pdf])

class Branch(Content):
    is_factory = models.BooleanField(default=False, help_text='عنوان المصنع يُدار من إعدادات الموقع')
    address_ar = models.TextField(blank=True)
    address_en = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

class SiteSettings(models.Model):
    title_ar = models.CharField(max_length=200, default='مصنع الدافنية للأنابيب')
    title_en = models.CharField(max_length=200, default='Adafnia Pipe Factory')
    tagline_ar = models.CharField(max_length=250, blank=True)
    tagline_en = models.CharField(max_length=250, blank=True)
    about_ar = models.TextField(blank=True)
    about_en = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    whatsapp = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address_ar = models.TextField(blank=True)
    address_en = models.TextField(blank=True)
    profile = models.FileField(upload_to=upload_path, validators=[validate_resource_pdf], blank=True)
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title_ar

class Enquiry(models.Model):
    name = models.CharField('الاسم', max_length=150)
    phone = models.CharField('الهاتف', max_length=50)
    email = models.EmailField('البريد الإلكتروني', blank=True)
    subject = models.CharField('الموضوع', max_length=250)
    message = models.TextField('الرسالة', max_length=10000)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.name} — {self.subject}'

class SubmissionThrottle(models.Model):
    key = models.CharField(max_length=64, unique=True)
    started_at = models.DateTimeField(default=timezone.now)
    count = models.PositiveIntegerField(default=0)


# Uploaded files follow their records: deleting a record, clearing a file or uploading a replacement
# removes the old file so the hosting account does not fill with orphans.
from django.db import transaction
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver


def _file_names(instance):
    return {f.name: getattr(instance, f.name).name for f in instance._meta.fields if isinstance(f, models.FileField)}


def _remove_later(storage, name):
    if name:
        transaction.on_commit(lambda: storage.exists(name) and storage.delete(name))


@receiver(pre_save)
def remove_replaced_files(sender, instance, **kwargs):
    if sender._meta.app_label != 'factory' or not instance.pk:
        return
    old = sender.objects.filter(pk=instance.pk).first()
    if old is None:
        return
    new_names = _file_names(instance)
    for field, name in _file_names(old).items():
        if name and name != new_names.get(field):
            _remove_later(getattr(old, field).storage, name)


@receiver(post_delete)
def remove_deleted_files(sender, instance, **kwargs):
    if sender._meta.app_label != 'factory':
        return
    for field, name in _file_names(instance).items():
        _remove_later(getattr(instance, field).storage, name)
