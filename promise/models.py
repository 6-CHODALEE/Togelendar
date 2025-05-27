from django.db import models
from account.models import User

# Create your models here.
class Promise(models.Model):
    promise_name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

class PromiseVote(models.Model):
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    selected_date = models.DateField()
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('username', 'promise', 'selected_date') # 중복 투표 방지