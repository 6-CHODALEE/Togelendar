from django.urls import path
from . import views

app_name = 'promise'

urlpatterns = [
    path('promise/', views.promise, name = 'promise'),
    path('promise/vote/', views.promise_vote, name = 'promise_vote'),
    path('promise/vote/result', views.promise_result, name = 'promise_result'),
]