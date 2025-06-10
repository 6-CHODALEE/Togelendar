from django.urls import path, include
from . import views

app_name = 'promise'

urlpatterns = [
    path('<int:promise_id>/promiselocation', include('promiselocation.urls')),

    path('', views.create_promise, name = 'create_promise'),
    path('no_place_promise/', views.no_place_promise, name = 'no_place_promise'),
    path('<int:promise_id>/vote/', views.promise_vote, name = 'promise_vote'),
    path('<int:promise_id>/result', views.promise_result, name = 'promise_result'),
    path('<int:promise_id>/delete/', views.delete_promise, name='delete_promise'),
]