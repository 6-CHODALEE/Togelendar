from django.urls import path
from .views import NotificationListView, NotificationMarkAllReadview, UnreadNotificationCountView, NotificationListAPIView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('mark_all_read/', NotificationMarkAllReadview.as_view(), name='notification-all-read'),
    path('unread_count/', UnreadNotificationCountView.as_view(), name='notification-unread-count'),
    path('api/notifications/', NotificationListAPIView.as_view(), name='notification-list-api'),
]