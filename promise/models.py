from django.db import models
from account.models import User
from mypage.models import CreateCommunity

# Create your models here.
class Promise(models.Model):
    community = models.ForeignKey(
        CreateCommunity,
        on_delete = models.CASCADE,
        related_name='promises'
    )
    promise_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.promise_name

class PromiseVote(models.Model):
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    selected_date = models.DateField()
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('username', 'promise', 'selected_date') # 중복 투표 방지