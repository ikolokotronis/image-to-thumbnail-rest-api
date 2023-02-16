from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User Model
    """

    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    tier = models.ForeignKey("Tier", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.username


class Tier(models.Model):
    """
    This model is used to store the different tiers a user can have.
    """

    name = models.CharField(max_length=255)
    thumbnail_height = models.IntegerField(
        null=True, blank=True
    )
    presence_of_original_file_link = models.BooleanField()
    ability_to_fetch_expiring_link = models.BooleanField()

    def __str__(self):
        return self.name
