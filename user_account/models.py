from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django_resized import ResizedImageField

# from django_resized import ResizedImageField

# Create your models here.
class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, primary_key=True)
    postcode = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_image = ResizedImageField(
        size=[500, 500],
        crop=['middle', 'center'],
        upload_to='profile/',
        default='profile/default.png',  # ✅ 기본 이미지 경로
        blank=True,
        null=True
    )