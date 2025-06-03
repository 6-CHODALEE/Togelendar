from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
import os
import dotenv
import requests


# .env 파일에서 환경변수 로드
dotenv.load_dotenv()

# 환경변수에서 API 키 불러오기
GOOGLE_API_KEY = os.environ.get('Google_API')
# Create your views here.

from django.conf import settings
from elasticsearch import Elasticsearch

def get_coordinates(address):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {
        'address': address,
        'key': GOOGLE_API_KEY,
    }

    response = requests.get(url, params=params)
    print(response.status_code)
    print(response.text)  # 🔥 응답 전체 보기
    if response.status_code == 200:
        result = response.json()
        if result['results']:
            location = result['results'][0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            return lng, lat  # 경도, 위도
    return 126.978219, 37.566588  # 실패 시
    


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            lng, lat = get_coordinates(form.cleaned_data['address'])  # ✅ 수정
            user.longitude = lng
            user.latitude = lat

            user.save()  # 🔥 이제 최종 저장

            # Elasticsearch 색인
            es = settings.ES_CLIENT
            es.index(index='user-index', id=user.id, body={
                'username': user.username,
                'email': user.email,
                'address': user.address,  # user.address는 모델 필드임
            })

            return redirect('account:login')

    else:
        form = CustomUserCreationForm()

    context = {
        'form': form
    }
    return render(request, 'signup.html', context)

def login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('mypage:mypage', username=user.username)
    else:
        form = CustomAuthenticationForm()

    context = {
        'form':form,
    }
    return render(request, 'login.html', context)


@login_required
def logout(request):
    auth_logout(request)
    return redirect('index:index')