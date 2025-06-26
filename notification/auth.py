# notification/auth.py
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import SAFE_METHODS

class ConditionalSessionAuthentication(SessionAuthentication):
    """
    GET/HEAD/OPTIONS 요청에만 CSRF 검사를 건너뛰고,
    그 외 POST/PATCH/DELETE 등은 기본 enforce_csrf 동작을 유지합니다.
    """
    def enforce_csrf(self, request):
        # 안전 메서드라면 CSRF 통과
        if request.method in SAFE_METHODS:
            return

        # 그 외에는 기본 로직으로 CSRF 검사
        return super().enforce_csrf(request)