from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import CreateCommunityFrom
from elasticsearch import Elasticsearch
from django.conf import settings
from .models import FriendRequest, CommunityMember, CreateCommunity
from django.contrib.auth import get_user_model
import json
from django.http import JsonResponse
from django.db.models import Q

User = get_user_model()
# Create your views here.

@login_required
def mypage(request, username):
    me = request.user

    # ✅ 받은 친구 요청 리스트
    received_requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user')

    # ✅ 내가 참여 중인 커뮤니티들 가져오기
    my_memberships = CommunityMember.objects.filter(member=me.username)

    # ✅ CreateCommunity에서 해당 커뮤니티 정보 가져오기
    my_communities = []
    for membership in my_memberships:
        community = CreateCommunity.objects.filter(
            community_name=membership.community_name,
            create_user=membership.create_user
        ).first()
        if community:
            my_communities.append(community)

    friend_list = FriendRequest.objects.filter(
        Q(from_user=me) | Q(to_user=me),
        status='accepted'
    )
    friend_count = friend_list.count()

    context = {
        'me': me,
        'received_requests': received_requests,
        'communities': my_communities,
        'friend_count': friend_count,
        'friend_list': friend_list,
    }

    return render(request, 'mypage.html', context)


@login_required
def create_community(request, username):
    if request.method == 'POST':
        form = CreateCommunityFrom(request.POST, request.FILES)
        if form.is_valid():
            community = form.save(commit=False)
            community.create_user = request.user.username
            community.save()

            # ✅ 생성자 본인을 멤버로 자동 추가
            CommunityMember.objects.create(
                community_name=community.community_name,
                create_user=community.create_user,
                member=request.user.username
            )

            return redirect('mypage:mypage', username=username)
    else:
        form = CreateCommunityFrom()
    
    return render(request, 'create_community.html', {'form': form})


from .models import FriendRequest

def search_friends(request, username):
    query = request.GET.get('q', '').strip()
    results = []
    popup_open = False

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

        for hit in hits:
            user_data = hit['_source']
            target_username = user_data['username']

            # ✅ 나 자신은 제외
            if target_username == request.user.username:
                continue

            try:
                to_user = User.objects.get(username=target_username)

                # ✅ 이미 친구인 경우 제외 (양방향 체크)
                is_friend = FriendRequest.objects.filter(
                    (
                        Q(from_user=request.user, to_user=to_user) |
                        Q(from_user=to_user, to_user=request.user)
                    ),
                    status='accepted'
                ).exists()

                if is_friend:
                    continue

                # ✅ 현재 요청 상태 체크
                friend_request = FriendRequest.objects.filter(from_user=request.user, to_user=to_user).first()
                if friend_request:
                    request_status = friend_request.status
                else:
                    request_status = None

                results.append({
                    'username': target_username,
                    'email': user_data.get('email', ''),
                    'request_status': request_status,
                })

            except User.DoesNotExist:
                continue  # ES에는 있는데 DB에는 없는 경우 skip

    received_requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user')

    context = {
        'me': username,
        'query': query,
        'results': results,
        'received_requests': received_requests,
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

        existing_request = FriendRequest.objects.filter(from_user=from_user, to_user=to_user).first()

        if existing_request:
            if existing_request.status == 'pending':
                return JsonResponse({'success': False, 'error': '이미 요청을 보냈습니다.'})
            elif existing_request.status == 'rejected':
                # 기존 요청을 재사용: 상태를 pending으로 바꿔서 다시 활성화
                existing_request.status = 'pending'
                existing_request.save()
                return JsonResponse({'success': True})
            elif existing_request.status == 'accepted':
                return JsonResponse({'success': False, 'error': '이미 친구입니다.'})
        else:
            FriendRequest.objects.create(from_user=from_user, to_user=to_user, status='pending')
            return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': '잘못된 요청 방식입니다.'})


@require_POST
@login_required
def send_friend_accept(request, username):
    if username != request.user.username:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)

    data = json.loads(request.body)
    from_username = data.get('from_username')
    to_user = request.user
    try:
        from_user = User.objects.get(username=from_username)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': '요청한 유저를 찾을 수 없습니다.'})

    try:
        friend_request = FriendRequest.objects.get(from_user=from_user, to_user=to_user, status='pending')
    except FriendRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': '친구 요청이 존재하지 않습니다.'})

    # 요청 상태 변경
    friend_request.status = 'accepted'
    friend_request.save()

    return JsonResponse({'success': True})



@login_required
def send_friend_reject(request, username):
    if username != request.user.username:
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        from_username = data.get('from_username')
        to_user = request.user

        try:
            from_user = User.objects.get(username=from_username)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': '요청한 유저를 찾을 수 없습니다.'})

        try:
            friend_request = FriendRequest.objects.get(from_user=from_user, to_user=to_user, status='pending')
        except FriendRequest.DoesNotExist:
            return JsonResponse({'success': False, 'error': '친구 요청이 존재하지 않습니다.'})

        friend_request.status = 'rejected'
        friend_request.save()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': '잘못된 요청 방식입니다.'})