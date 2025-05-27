from django.urls import path
from . import views

app_name = 'mypage'

urlpatterns = [
    path('<str:username>/', views.mypage, name='mypage'),
    path('<str:username>/createcommunity/', views.createcommunity, name='createcommunity'),
    path('<str:username>/search_friends/', views.search_friends, name='search_friends'),

    path('<str:username>/friend/request/', views.send_friend_request, name='send_friend_request'),
    path('<str:username>/friend/accept/', views.send_friend_accept, name='send_friend_accept'),
    path('<str:username>/friend/reject/', views.send_friend_reject, name='send_friend_reject'),

]