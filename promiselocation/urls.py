from django.urls import path, include
from . import views

app_name = 'promiselocation'

urlpatterns = [
    path('', views.location, name = 'location'),
]