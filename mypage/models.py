from django.db import models
from django_resized import ResizedImageField
from django.conf import settings

# 커뮤니티 생성 정보 저장 모델
class CreateCommunity(models.Model):
    communityname = models.CharField(primary_key=True, max_length=100)  # 커뮤니티 이름 / pk로 지정
    createuser = models.CharField(max_length=100)  # 커뮤니티 생성자 (길이 제한 추가)
    communityintro = models.TextField()  # 커뮤니티 소개
    communityimage = ResizedImageField(
        size=[500, 500],
        crop=['middle', 'center'],
        upload_to='mypage/mypage_image/',
        quality=90,
        force_format='JPEG'
    )  # 커뮤니티 대표 이미지 저장

    def __str__(self):
        return self.communityname



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