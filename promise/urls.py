from django.urls import path
from . import views

app_name = 'promise'

urlpatterns = [
    path('promise/', views.promise, name = 'promise'),
]