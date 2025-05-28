from django.urls import path
from . import views

app_name = 'promise'

urlpatterns = [
    path('<int:community_id>/promise/', views.create_promise, name = 'create_promise'),
    path('<int:community_id>/promise/<int:promise_id>/vote/', views.promise_vote, name = 'promise_vote'),
    path('<int:community_id>/promise/<int:promise_id>/result', views.promise_result, name = 'promise_result'),
]