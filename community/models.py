from django.db import models
from django.conf import settings
from user_account.models import User
from mypage.models import CreateCommunity
from promise.models import Promise
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

# Create your models here.
class CommunityMember(models.Model):
    id = models.AutoField(primary_key=True)  # 기본 PK 필드
    community_name = models.CharField(max_length=100)
    create_user = models.CharField(max_length=100)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_members'
    )

    def __str__(self):
        return f"{self.member} in {self.community_name} (created by {self.create_user})"

class CommunityInvite(models.Model):
    community = models.ForeignKey(
        CreateCommunity, 
        on_delete=models.CASCADE)
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="sent_invites")
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "received_invites")
    status = models.CharField(
        max_length=10,
        choices = [('pending', '대기중'), ('accepted', '수락됨'), ('rejected', '거절됨')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('community', 'to_user')

    def __str__(self):
        return f"{self.to_user.username}에게 {self.community.community_name}초대"

class Photo(models.Model):
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='album/photos/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_main = models.BooleanField(default=False)

class MoodVote(models.Model):
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 중복투표 방지
        unique_together = ('promise', 'user')

class PhotoComment(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)



@receiver(post_delete, sender=Photo)
def delete_image_file(sender, instance, **kwargs):
    try:
        if instance.image and hasattr(instance.image, 'path'):
            if os.path.isfile(instance.image.path):
                os.remove(instance.image.path)
    except Exception as e:
        # 로그 출력 또는 무시할 수 있음
        print(f"이미지 삭제 중 오류 발생: {e}")