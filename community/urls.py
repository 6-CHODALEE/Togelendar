from django.urls import path, include
from . import views

app_name = 'community'

urlpatterns = [
    path('<int:community_id>/promise/', include('promise.urls')),

    path('<int:community_id>/', views.community_detail, name = 'community_detail'),
    path('<int:community_id>/update_image', views.update_image, name='update_image'),
    # ajax : asynchromous javascript and xml => 페이지 전체를 새로고침하지 않고, 서버에 데이터를 주고 받는 기술
    path('<int:community_id>/invite_member/', views.invite_member_ajax, name = 'invite_member_ajax'),
    ]