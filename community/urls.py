from django.urls import path, include
from . import views

app_name = 'community'

urlpatterns = [
    path('<int:community_id>/', views.community_detail, name = 'community_detail'),
    ]