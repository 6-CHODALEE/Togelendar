from django.core.management.base import BaseCommand
from user_account.models import User
from mypage.models import FriendRequest, CreateCommunity
from community.models import CommunityMember
from django.core.files import File
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os
from itertools import combinations

# .env 로드
load_dotenv()
ES_PASSWORD = os.getenv('ES_PASSWORD')

DOWNLOADS_DIR = os.path.expanduser('/Users/jungseok/Downloads')

class Command(BaseCommand):
    help = '테스트 사용자 5명 생성 + Elasticsearch 색인 + 친구 관계 + 커뮤니티 자동 생성'

    def handle(self, *args, **options):
        # es = Elasticsearch(
        #     ['https://localhost:9200'],
        #     # basic_auth=('elastic', ES_PASSWORD),
        #     verify_certs=False
        # )

        dummy_users = [
            {
                'username': '짱구',
                'email': 'zzanggu@google.com',
                'password': 'zzanggu1234',
                'postcode': '02798',
                'address': '서울 성북구 종암로24길 35',
                'latitude': 37.601880,
                'longitude': 127.034838,
                'profile_image_path': os.path.join(DOWNLOADS_DIR, '감성 인물 사진1.jpg'),
            },
            {
                'username': '철수',
                'email': 'chulsu@google.com',
                'password': 'chulsu1234',
                'postcode': '04419',
                'address': '서울 용산구 독서당로 111',
                'latitude': 37.537159,
                'longitude': 127.009426,
                'profile_image_path': os.path.join(DOWNLOADS_DIR, '감성 인물 사진2.png'),
            },
            {
                'username': '맹구',
                'email': 'manggoo@google.com',
                'password': 'manggoo1234',
                'postcode': '06284',
                'address': '서울 강남구 삼성로 212',
                'latitude': 37.497588,
                'longitude': 127.065306,
                'profile_image_path': os.path.join(DOWNLOADS_DIR, '감성 인물 사진3.png'),
            },
            {
                'username': '훈이',
                'email': 'hooni@google.com',
                'password': 'hooni1234',
                'postcode': '05551',
                'address': '서울 송파구 올림픽로 300',
                'latitude': 37.513262,
                'longitude': 127.103412,
                'profile_image_path': os.path.join(DOWNLOADS_DIR, '감성 인물 사진4.jpeg'),
            },
            {
                'username': '유리',
                'email': 'yoori@google.com',
                'password': 'yoori1234',
                'postcode': '02559',
                'address': '서울 동대문구 답십리로 27',
                'latitude': 37.580088,
                'longitude': 127.046430,
                'profile_image_path': os.path.join(DOWNLOADS_DIR, '감성 인물 사진5.jpg'),
            },
        ]

        created_users = {}

        for user_data in dummy_users:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                )
                user.postcode = user_data['postcode']
                user.address = user_data['address']
                user.latitude = user_data['latitude']
                user.longitude = user_data['longitude']

                profile_path = user_data.get('profile_image_path')
                if profile_path and os.path.exists(profile_path):
                    with open(profile_path, 'rb') as img_file:
                        user.profile_image.save(
                            os.path.basename(profile_path),
                            File(img_file),
                            save=False
                        )
                user.save()
                self.stdout.write(self.style.SUCCESS(f"{user.username} 생성 완료"))
            else:
                user = User.objects.get(username=user_data['username'])
                self.stdout.write(self.style.WARNING(f"{user.username} 이미 존재함"))

            # es.index(
            #     index='user-index',
            #     id=user.username,
            #     document={
            #         'username': user.username,
            #         'email': user.email,
            #         'address': user.address,
            #     }
            # )
            # self.stdout.write(self.style.SUCCESS(f"{user.username} -> Elasticsearch 색인 완료"))
            # created_users[user.username] = user

        for u1, u2 in combinations(created_users.values(), 2):
            fr, created = FriendRequest.objects.get_or_create(
                from_user=u1,
                to_user=u2,
                defaults={'status': 'accepted'}
            )
            if not created and fr.status != 'accepted':
                fr.status = 'accepted'
                fr.save()
        self.stdout.write(self.style.SUCCESS("🎉 모든 유저 간 친구 관계 10개 생성 완료"))