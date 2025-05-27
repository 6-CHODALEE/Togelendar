from django.urls import path, include
from . import views

app_name = 'community'

urlpatterns = [
    path('community/', views.community, name = 'community'),
    path('community/', include('promise.urls')),
    ]