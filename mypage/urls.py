from django.urls import path, include
from . import views

app_name = 'mypage'

urlpatterns = [
    # path('togelendar/mypage/<str:username>/community/', include(('community.urls', 'community'), namespace='community')),



    path('<str:username>/', views.mypage, name='mypage'),
    path('<str:username>/verify_password/', views.verify_password, name='verify_password'),
    path('<str:username>/myprofile/', views.myprofile, name='myprofile'),
    path('<str:username>/create_community/', views.create_community, name='create_community'),
    path('<str:username>/search_friends/', views.search_friends, name='search_friends'),

    path('<str:username>/friend/request/', views.send_friend_request, name='send_friend_request'),
    path('<str:username>/friend/accept/', views.send_friend_accept, name='send_friend_accept'),
    path('<str:username>/friend/reject/', views.send_friend_reject, name='send_friend_reject'),

    path('<str:username>/respond_invite/', views.respond_invite, name='respond_invite'),
    path('<str:username>/set_color/<int:community_id>/', views.set_user_community_color, name='set_community_color'),

]