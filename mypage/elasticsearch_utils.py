# ✅ 수정된 elasticsearch_utils.py
from django.conf import settings

ES_CLIENT = settings.ES_CLIENT  # settings.py에서 정의한 ES_CLIENT 가져오기

def update_user_index(user):
    ES_CLIENT.index(
        index='user-index',
        id=user.username,
        body={
            "username": user.username,
            "email": user.email,
            "address": user.address,
            "postcode": user.postcode,
        }
    )

def delete_user_index(username):
    try:
        if ES_CLIENT.exists(index='user-index', id=username):
            ES_CLIENT.delete(index='user-index', id=username)
            print(f"[Elastic] 삭제 완료: {username}")
        else:
            print(f"[Elastic] 삭제 건너뜀: {username} 인덱스 없음")
    except Exception as e:
        print(f"[Elastic] 삭제 중 오류 발생 ({username}): {e}")