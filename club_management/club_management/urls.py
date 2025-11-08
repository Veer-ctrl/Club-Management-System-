from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render


def landing_page(request):
    return render(request, 'landing.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', landing_page, name='landing_page'),
    path('', include('users.urls')),
    # path('applications/', include('applications.urls')),
    path('clubs/', include('clubs.urls')),
    # path('events/', include('Events.urls')),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)