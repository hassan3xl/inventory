    
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('router.urls')),
    
    # Web views (Platform Admin)
    path('auth/', include('apps.users.web_urls')),
    path('', include('apps.tenants.web_urls')),
]
