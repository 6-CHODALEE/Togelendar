from django.db import models
from django_resized import ResizedImageField
from django.conf import settings
from user_account.models import User

from django.apps import apps
# 커뮤니티 생성 정보 저장 모델
class CreateCommunity(models.Model):
    id = models.AutoField(primary_key=True)
    community_name = models.CharField(max_length=100, unique=True)
    create_user = models.ForeignKey(User, to_field = 'username', on_delete = models.CASCADE)
    community_intro = models.TextField()
    community_image = ResizedImageField(
        size=[500, 500],
        crop=None,
        upload_to='mypage/mypage_image/',
        quality=90,
        force_format='JPEG'
    )

    def __str__(self):
        return f"{self.community_name} (ID: {self.id})"



class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_requests',
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='received_requests',
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', '대기중'),
            ('accepted', '수락됨'),
            ('rejected', '거절됨')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"



class CommunityColor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    community = models.ForeignKey('mypage.CreateCommunity', on_delete=models.CASCADE)
    custom_color = models.CharField(max_length=7, default="#FFB8FF")

    class Meta:
        unique_together = ('user', 'community')