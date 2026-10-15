from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import RedirectView
from factory import views, dashboard, seo

urlpatterns = [
    path('robots.txt', seo.robots, name='robots'),
    path('sitemap.xml', seo.sitemap, name='sitemap'),
    path('', RedirectView.as_view(url='/ar/', permanent=False)),
    path('admin/', admin.site.urls),
    path('dashboard/login/', dashboard.DashboardLogin.as_view(), name='dashboard-login'),
    path('dashboard/logout/', LogoutView.as_view(), name='dashboard-logout'),
    path('dashboard/', dashboard.index, name='dashboard'),
    path('dashboard/<str:section>/', dashboard.listing, name='dashboard-list'),
    path('dashboard/<str:section>/new/', dashboard.edit, name='dashboard-create'),
    path('dashboard/<str:section>/<int:pk>/edit/', dashboard.edit, name='dashboard-edit'),
    path('dashboard/<str:section>/<int:pk>/delete/', dashboard.delete, name='dashboard-delete'),
    path('<str:lang>/', views.page, name='home'),
    path('<str:lang>/api/variants/', views.variants, name='variants-api'),
]
for page in ['about', 'products', 'news', 'projects', 'quality', 'resources', 'contact']:
    urlpatterns.append(path(f'<str:lang>/{page}/', views.page, {'page': page}, name=page))
for route, page in [('products', 'product_detail'), ('news', 'news_detail'), ('projects', 'project_detail')]:
    urlpatterns.append(path(f'<str:lang>/{route}/<slug:slug>/', views.page, {'page': page}, name=page))
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
