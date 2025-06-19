from django.db import models
from django.contrib.auth.models import AbstractUser
from django_resized import ResizedImageField
import random

# from django_resized import ResizedImageField

# Create your models here.

def get_random_default_image():
    choices = [
        'profile/pink_diary_character.png',
        'profile/diary_character.png',
        'profile/polaroid_character.png',
    ]
    return random.choice(choices)

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    postcode = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    profile_image = ResizedImageField(
        size=[500, 500],
        crop=['middle', 'center'],
        upload_to='profile/',
        default=get_random_default_image,  # 기본 이미지 경로
        blank=True,
        null=True
    )