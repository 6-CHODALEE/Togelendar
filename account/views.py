from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required

# Create your views here.

def index(request):
    return render(request, 'index.html')

from django.conf import settings
from elasticsearch import Elasticsearch

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()  # 🔥 유저 인스턴스 받아오기

            # Elasticsearch 색인
            es = settings.ES_CLIENT
            es.index(index='user-index', id=user.id, body={
                'username': user.username,
                'email': user.email,
                'address': user.address,  # 별도 필드가 있다면 추가
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
    return redirect('account:index')