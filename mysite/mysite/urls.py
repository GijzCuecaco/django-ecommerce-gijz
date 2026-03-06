from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Django's built-in auth URLs
    path('', include('homepage.urls')),  # include homepage app URLs
]

# Serve media files (both development and production)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)