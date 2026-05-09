from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import FileResponse
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('core.urls')),
    path('sw.js', lambda r: FileResponse(open(os.path.join('static', 'sw.js'), 'rb'), content_type='application/javascript')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
