

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from soporte.views import logout_view  

urlpatterns = [
    # 1) raíz → users.urls
    path('', include('users.urls')),

    # 2) /soporte/... → soporte.urls
    path('soporte/', include('soporte.urls')),

    # 3) admin
    path('admin/', admin.site.urls),

    path('messenger/', include('messenger.urls')),

    path('logout/', logout_view, name='logout'),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
