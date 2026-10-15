from django import forms
from django.utils import translation
from .models import Enquiry, Product

class EnquiryForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    class Meta:
        model = Enquiry
        fields = ['name', 'phone', 'email', 'subject', 'message', 'product']
    def __init__(self, *args, **kwargs):
        self.lang = kwargs.pop('lang', 'ar')
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
        self.fields['product'].queryset = Product.objects.filter(is_published=True)
        labels = {'name': ('الاسم', 'Name'), 'phone': ('الهاتف', 'Phone'), 'email': ('البريد الإلكتروني', 'Email'), 'subject': ('الموضوع', 'Subject'), 'message': ('الرسالة', 'Message'), 'product': ('المنتج', 'Product')}
        for name, pair in labels.items():
            self.fields[name].label = pair[self.lang == 'en']
        self.fields['product'].empty_label = 'Select a product (optional)' if self.lang == 'en' else 'اختر منتجاً (اختياري)'
        self.fields['product'].label_from_instance = lambda obj: (obj.title_en or obj.title_ar) if self.lang == 'en' else (obj.title_ar or obj.title_en)
    def full_clean(self):
        with translation.override(self.lang):
            return super().full_clean()
    def clean_phone(self):
        value = self.cleaned_data['phone'].strip()
        if sum(c.isdigit() for c in value) < 6:
            raise forms.ValidationError('Enter a valid phone number.' if self.lang == 'en' else 'أدخل رقم هاتف صالحاً.')
        return value
