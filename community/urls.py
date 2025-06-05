from django.urls import path, include
from . import views

app_name = 'community'

urlpatterns = [
    path('<int:community_id>/promise/', include('promise.urls')),

    path('<int:community_id>/', views.community_detail, name = 'community_detail'),
    path('<int:community_id>/update_image/', views.update_image, name='update_image'),
    path('<int:community_id>/update_info/', views.update_community_info, name='update_community_info'),
    # ajax : asynchromous javascript and xml => 페이지 전체를 새로고침하지 않고, 서버에 데이터를 주고 받는 기술
    path('<int:community_id>/invite_member/', views.invite_member_ajax, name = 'invite_member_ajax'),

    path('<int:community_id>/album/<str:album_name>', views.album_detail, name='album_detail'),
    path('<int:community_id>/album/<str:album_name>/upload/', views.upload_photo, name='upload_photo'),
    path('<int:community_id>/album/<str:album_name>/mood_vote/', views.mood_vote, name='mood_vote'),
    path('<int:community_id>/album/<str:album_name>/<str:photo_id>/comment/', views.photo_comment, name='photo_comment'),
    ]