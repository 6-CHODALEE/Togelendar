from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from .models import Notification
from .serializers import NotificationSerializer
from .utils import NotificationPagination
from datetime import timedelta
from django.utils import timezone
from .auth import ConditionalSessionAuthentication


# Create your views here.

# 알림 목록 조회
class NotificationListView(ListAPIView):
    authentication_classes = [ConditionalSessionAuthentication]
    permission_classes     = [IsAuthenticated]
    serializer_class       = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:10]

# 모든 알림 읽음 처리
class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "모든 알림을 읽음 처리 했습니다."}, status=status.HTTP_200_OK)

# 링크를 들어갔을 때 한 알림 읽음 처리
class NotificationMarkOneReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'status': 'success'})
        except Notification.DoesNotExist:
            return Response({'status': 'not found'}, status=404)
        

# 안 읽은 알림 수 조회
class UnreadNotificationCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count" : count})

class NotificationListAPIView(generics.ListAPIView):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer
    pagination_class = NotificationPagination

    # 최근 일주일 알림만 보이게
    def get_queryset(self):
        seven_days_ago = timezone.now() - timedelta(days=7)
        return Notification.objects.filter(
            user=self.request.user, 
            created_at__gte=seven_days_ago
        ).order_by('-created_at')