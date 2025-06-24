from django.db import models
from django.contrib.auth import get_user_model
from mypage.models import CreateCommunity
from promise.models import Promise
from community.models import Photo

# Create your models here.
User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_member', '새 멤버'),
        ('new_promise', '새 약속'),
        ('vote_complete', '투표 완료'),
        ('place_selected', '장소 선택'),
        ('photo_comment', '사진 댓글'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'notification')
    notification_type = models.CharField(max_length=30, choices = NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)
    url = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    community = models.ForeignKey(CreateCommunity, null=True, blank=True, on_delete=models.CASCADE)
    promise = models.ForeignKey(Promise, null=True, blank=True, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {'읽음' if self.is_read else '안읽음'}"