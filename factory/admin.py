from django.contrib import admin
from . import models
for model in (models.Category, models.Product, models.ProductVariant, models.NewsArticle, models.Project, models.Certificate, models.Resource, models.Branch, models.SiteSettings, models.Enquiry):
    admin.site.register(model)
