from django.db import models
from user_account.models import User
from mypage.models import CreateCommunity

# Create your models here.
class Promise(models.Model):
    community = models.ForeignKey(
        CreateCommunity,
        on_delete = models.CASCADE,
        related_name='promises'
    )
    promise_name = models.CharField(max_length=100, null=True)
    promise_creator = models.CharField(max_length=150, null=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.promise_name
    
    @property
    def main_photo(self):
        return self.photo_set.filter(is_main=True).first()


class PromiseVote(models.Model):
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    promise_name = models.CharField(max_length=100, null=True)
    selected_date = models.DateField()
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('username', 'promise', 'selected_date') # 중복 투표 방지


class PromiseResult(models.Model):
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    promise_name = models.CharField(max_length=100, null=True)
    promise_creator = models.CharField(max_length=100, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    center_latitude = models.FloatField(null=True, blank=True)
    center_longitude = models.FloatField(null=True, blank=True)
    places_json = models.JSONField(null=True, blank=True)