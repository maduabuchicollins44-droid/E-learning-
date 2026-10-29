from academy import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # 1. Django Admin Panel
    path('admin/', admin.site.urls),
    
    # 2. Custom Login Override (Must come BEFORE django.contrib.auth.urls)
    path('accounts/login/', views.custom_login, name='login'),
    
    # 3. Built-in Authentication URLs (logout, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # 4. Academy App URLs
    path('', include('academy.urls')),
]

# Serve static & user-uploaded media files in development mode
if settings.DEBUG:
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
