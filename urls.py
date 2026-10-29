from academy import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # 1. Django Admin Panel
    path('admin/', admin.site.urls),
    
    # 2. Override default login route BEFORE auth.urls
    path('accounts/login/', views.custom_login, name='login'),
    
    # 3. Built-in auth URLs (logout, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # 4. Academy app routes
    path('', include('academy.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
