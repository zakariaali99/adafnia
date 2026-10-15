from pathlib import Path
from uuid import uuid4
from django.core.exceptions import ValidationError
from PIL import Image

def upload_path(instance, filename):
    return f'uploads/{uuid4().hex}{Path(filename).suffix.lower()}'

def validate_image(value):
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('الحد الأقصى للصورة 5 ميغابايت.')
    if Path(value.name).suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
        raise ValidationError('اختر صورة JPEG أو PNG أو WebP.')
    try:
        position = value.tell()
        value.seek(0)
        with Image.open(value) as image:
            if image.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('Unsupported format')
            image.verify()
        value.seek(position)
    except Exception as exc:
        raise ValidationError('ملف الصورة غير صالح.') from exc

def validate_pdf(value, max_mb=10):
    if value.size > max_mb * 1024 * 1024:
        raise ValidationError(f'الحد الأقصى للملف {max_mb} ميغابايت.')
    position = value.tell()
    value.seek(0)
    header = value.read(5)
    value.seek(position)
    if Path(value.name).suffix.lower() != '.pdf' or header != b'%PDF-':
        raise ValidationError('اختر ملف PDF صالحاً.')

def validate_resource_pdf(value):
    validate_pdf(value, max_mb=32)
