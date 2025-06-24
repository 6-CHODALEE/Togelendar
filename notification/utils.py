from .models import Notification
from rest_framework.pagination import PageNumberPagination

def notify(users, verb, message, url=''):
    for user in users:
        Notification.objects.create(user=user, verb=verb, message=message, url=url)

class NotificationPagination(PageNumberPagination):
    page_size = 5