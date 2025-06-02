from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

# from django_resized import ResizedImageField

# Create your models here.
class User(AbstractUser):
    postcode = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=255, blank=True)
