from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CreateCommunityFrom
from elasticsearch import Elasticsearch
from django.conf import settings
from .models import FriendRequest
from django.contrib.auth import get_user_model
import json
from django.http import JsonResponse

User = get_user_model()
# Create your views here.

@login_required
def mypage(request, username):
    me = request.user

    # ✅ 받은 친구 요청 리스트 추가
    received_requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user')

    context = {
        'me': me,
        'received_requests': received_requests  # ✅ 추가
    }
    return render(request, 'mypage.html', context)


def createcommunity(request, username):
    if request.method == 'POST':
        form = CreateCommunityFrom(request.POST, request.FILES)
        if form.is_valid():
            communityinfo = form.save(commit=False)
            communityinfo.createuser = request.user.username
            communityinfo.save()
            return redirect('mypage:mypage', username=request.user.username)
    else:
        form = CreateCommunityFrom()

    context = {
        'form' : form,
        'username': username
    }
    return render(request, 'createcommunity.html', context)


from .models import FriendRequest

def search_friends(request, username):
    query = request.GET.get('q', '').strip()
    results = []
    popup_open = False  # 기본 닫힘

    if query:
        popup_open = request.GET.get('popup_open', 'false') == 'true'
        response = settings.ES_CLIENT.search(
            index="user-index",
            body={
                "query": {
                    "match": {
                        "username": query
                    }
                }
            }
        )
        hits = response['hits']['hits']
        results = [hit['_source'] for hit in hits]

    # ✅ 현재 로그인 사용자에게 들어온 pending 요청들
    received_requests = FriendRequest.objects.filter(
    to_user=request.user,
    status='pending'
    ).select_related('from_user')

    context = {
        'me': username,
        'query': query,
        'results': results,
        'received_requests': received_requests,  # ✅ 추가!
        'open_popover': popup_open
    }
    return render(request, 'mypage.html', context)


@login_required
def send_friend_request(request, username):
    if username != request.user.username:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        to_username = data.get('to_username')
        from_user = request.user

        try:
            to_user = User.objects.get(username=to_username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '대상 유저를 찾을 수 없습니다.'})

        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user, status='pending').exists():
            return JsonResponse({'success': False, 'error': '이미 요청을 보냈습니다.'})

        FriendRequest.objects.create(from_user=from_user, to_user=to_user, status='pending')
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': '잘못된 요청 방식입니다.'})