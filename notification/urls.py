from django.urls import path
from .views import NotificationListView, NotificationMarkAllReadView, NotificationMarkOneReadView, UnreadNotificationCountView, NotificationListAPIView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('mark_all_read/', NotificationMarkAllReadView.as_view(), name='notification-all-read'),
    path('mark_read/<int:pk>/', NotificationMarkOneReadView.as_view(), name='notification-mark-read'),
    path('unread_count/', UnreadNotificationCountView.as_view(), name='notification-unread-count'),
    path('api/notifications/', NotificationListAPIView.as_view(), name='notification-list-api'),
]