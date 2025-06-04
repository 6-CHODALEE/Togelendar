from django.db import models
from django.conf import settings
from mypage.models import CreateCommunity

# Create your models here.
class CommunityMember(models.Model):
    id = models.AutoField(primary_key=True)  # 기본 PK 필드
    community_name = models.CharField(max_length=100)
    create_user = models.CharField(max_length=100)
    member = models.CharField(max_length=100)

    class Meta:
        unique_together = ('community_name', 'member')

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
