from django.urls import path
from . import views

app_name = 'promiselocation'

urlpatterns = [
    path('<int:community_id>/promise/<int:promise_id>/result/location', views.location, name = 'location'),
]