from django.contrib import admin

from images.models import Image, ExpiringImage

admin.site.register(Image)
admin.site.register(ExpiringImage)
