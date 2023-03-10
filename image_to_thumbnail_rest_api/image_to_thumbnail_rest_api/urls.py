"""image_to_thumbnail_rest_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from images.views import ExpiringImageView, OpenImageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("images/", include("images.urls")),
    path("users/", include("users.urls")),
    path(
        "media/expiring-images/<str:file_name>",
        ExpiringImageView.as_view(),
        name="expiring-image-view",
    ),
    path(
        "media/<int:user_pk>/images/<str:file_name>",
        OpenImageView.as_view(),
        name="image-access",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
