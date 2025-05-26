from django.db import models

# Create your models here.
class Promise(models.Model):
    title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

class PromiseVote(models.Model):
    promise = models.ForeignKey(Promise, on_delete=models.CASCADE)
    date = models.DateField()
    # user = models.ForeignKey(User, on_delete=models.CASCADE)