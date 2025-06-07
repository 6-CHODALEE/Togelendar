from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import CreateCommunityFrom
from elasticsearch import Elasticsearch
from django.conf import settings
from .models import CreateCommunity, FriendRequest
from community.models import CommunityMember, CommunityInvite
from django.contrib.auth import get_user_model
import json
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime, timedelta, date
from django.utils.dateparse import parse_date
from community.models import CommunityMember
from collections import defaultdict
from promise.models import Promise, PromiseResult


User = get_user_model()
# Create your views here.

@login_required
def mypage(request, username):
    me = request.user

    # 📌 base_date GET 파라미터 처리
    # 안전하게 파싱
    base_date_str = request.GET.get('base_date')
    if base_date_str:
        try:
            base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
        except ValueError:
            base_date = date.today()
    else:
        base_date = date.today()

    days_since_sunday = (base_date.weekday() + 1) % 7
    start_of_week = base_date - timedelta(days=days_since_sunday)
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    weekday_labels = ['일', '월', '화', '수', '목', '금', '토']

    # 📌 이전/다음 주 계산용
    prev_week = base_date - timedelta(days=7)
    next_week = base_date + timedelta(days=7)

    # --- 이하 기존 코드 그대로 유지 ---
    received_requests = FriendRequest.objects.filter(
        to_user=me, status='pending'
    ).select_related('from_user')

    my_memberships = CommunityMember.objects.filter(member=me.username)
    my_communities = [
        CreateCommunity.objects.filter(
            community_name=m.community_name,
            create_user=m.create_user
        ).first()
        for m in my_memberships
    ]
    my_communities = [c for c in my_communities if c is not None]
    community_names = [c.community_name for c in my_communities]

    promises = Promise.objects.filter(community__community_name__in=community_names)
    results = PromiseResult.objects.filter(promise__in=promises)

    from collections import defaultdict
    weekly_promises = defaultdict(list)
    for result in results:
        current_date = result.start_date
        while current_date <= result.end_date:
            if current_date in week_dates:
                weekly_promises[current_date].append(result)
            current_date += timedelta(days=1)

    friend_list = FriendRequest.objects.filter(
        Q(from_user=me) | Q(to_user=me), status='accepted'
    )
    friend_count = friend_list.count()

    invite_requests = CommunityInvite.objects.filter(
        to_user=me, status='pending'
    )

    context = {
        'me': me,
        'received_requests': received_requests,
        'communities': my_communities,
        'friend_count': friend_count,
        'friend_list': friend_list,
        'invite_requests': invite_requests,
        'week_dates': week_dates,
        'weekday_labels': weekday_labels,
        'weekly_promises': weekly_promises,
        'base_date': base_date,
        'prev_week': prev_week.isoformat(),  
        'next_week': next_week.isoformat(),  
        'today': date.today(),
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

@require_POST
@login_required
def respond_invite(request, username):
    data = json.loads(request.body)
    invite_id = data.get("invite_id")
    action = data.get("action")

    try:
        invite = CommunityInvite.objects.get(id=invite_id)

        if action == "accept":
            # 멤버로 추가
            CommunityMember.objects.create(
                community_name=invite.community.community_name,
                create_user = invite.community.create_user,
                member = invite.to_user.username
            )
            invite.status = 'accepted'
        
        elif action == 'reject':
            invite.status = 'rejected'
        
        invite.save()
        return JsonResponse({'success': True})


    except CommunityInvite.DoesNotExist:
        return JsonResponse({'success': False, 'error': '초대 기록을 찾을 수 없습니다.'})