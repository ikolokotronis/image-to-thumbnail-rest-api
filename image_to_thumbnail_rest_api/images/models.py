from django.db import models


def image_upload_location(instance, filename, **kwargs):
    """
    Location for the image file
    """
    file_path = f"{instance.user.id}/images/{filename}"
    return file_path


def expiring_image_upload_location(instance, filename, **kwargs):
    """
    Location for the expiring image file
    """
    file_path = f"expiring-images/{filename}"
    return file_path


class ExpiringImage(models.Model):
    """
    This model is used to store images that are only accessible for a limited time, after which they are deleted.
    """

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=expiring_image_upload_location)
    live_time = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.image.url


class Image(models.Model):
    """
    This model is used to store images that are accessible for the user.
    """

    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    original_image = models.ImageField(upload_to=image_upload_location)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_image.url
