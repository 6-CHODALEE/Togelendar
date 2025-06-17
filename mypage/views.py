from django.shortcuts import render, redirect, get_object_or_404
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
from user_account.forms import CustomUserCreationForm, CustomAuthenticationForm
from .forms import ProfileUpdateForm
from .elasticsearch_utils import update_user_index, delete_user_index  # 유틸 함수 임포트
from django.contrib.auth import login, get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ProfileUpdateForm
from mypage.elasticsearch_utils import update_user_index, delete_user_index
from django.utils import timezone
from .forms import ProfileUpdateForm
from django.contrib.auth import authenticate
from .forms import PasswordCheckForm
from django.contrib.auth import get_user_model, login
from django.contrib.auth import get_backends
from django.http import JsonResponse
from django.contrib import messages


User = get_user_model()
# Create your views here.



@login_required
def mypage(request, username):
    me = request.user

    # base_date GET 파라미터 처리
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

    # 이전/다음 주 계산용
    prev_week = base_date - timedelta(days=7)
    next_week = base_date + timedelta(days=7)

    # --- 이하 기존 코드 그대로 유지 ---
    received_requests = FriendRequest.objects.filter(
        to_user=me, status='pending'
    ).select_related('from_user')

    my_memberships = CommunityMember.objects.filter(member=me.username)

    my_communities = [m.community_name for m in my_memberships]


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
            # 폼에서 추출만 (아직 저장은 안 함)
            temp_community_name = form.cleaned_data['community_name']
            temp_create_user = request.user.username

            community = form.save(commit=False)
            community.create_user = temp_create_user
            community.save()

        
            print(community.community_name)
            CommunityMember.objects.create(
                community_name=community,
                create_user=community.create_user,
                member=request.user
            )

            return redirect('mypage:mypage', username=username)
        else: 
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
            return render(request, 'create_community.html', {'form': form})
    else:
        form = CreateCommunityFrom()
    
    return render(request, 'create_community.html', {'form': form})


from .models import FriendRequest

def search_friends(request, username):
    query = request.GET.get('q', '').strip()
    popup_open = request.GET.get('popup_open', 'false') == 'true' 
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    results = []

    if query:
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

            if target_username == request.user.username:
                continue

            try:
                to_user = User.objects.get(username=target_username)

                # 친구인지 확인
                is_friend = FriendRequest.objects.filter(
                    (
                        Q(from_user=request.user, to_user=to_user) |
                        Q(from_user=to_user, to_user=request.user)
                    ),
                    status='accepted'
                ).exists()

                if is_friend:
                    continue

                request_status = None
                if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
                    request_status = 'pending'

                results.append({
                    'username': target_username,
                    'email': user_data.get('email', ''),
                    'request_status': request_status,
                })

            except User.DoesNotExist:
                continue

    # ✅ Ajax 요청이면 JSON 응답
    if is_ajax:
        return JsonResponse(results, safe=False)

    # 기존 mypage context 구성 추가
    me = request.user

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

    prev_week = base_date - timedelta(days=7)
    next_week = base_date + timedelta(days=7)

    received_requests = FriendRequest.objects.filter(to_user=me, status='pending').select_related('from_user')

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
    results_in_week = PromiseResult.objects.filter(promise__in=promises)

    from collections import defaultdict
    weekly_promises = defaultdict(list)
    for result in results_in_week:
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
        'friend_list': friend_list,
        'friend_count': friend_count,
        'communities': my_communities,
        'week_dates': week_dates,
        'base_date': base_date,
        'today': date.today(),
        'prev_week': prev_week.isoformat(),
        'next_week': next_week.isoformat(),
        'weekly_promises': weekly_promises,
        'weekday_labels': weekday_labels,
        'query': query,
        'results': results,
        'received_requests': received_requests,
        'open_popover': popup_open,
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
            CommunityMember.objects.create(
                community_name=invite.community.community_name,
                create_user=invite.community.create_user,
                member=invite.to_user  
            )
            invite.status = 'accepted'

        elif action == 'reject':
            invite.status = 'rejected'

        invite.save()
        return JsonResponse({'success': True})

    except CommunityInvite.DoesNotExist:
        return JsonResponse({'success': False, 'error': '초대 기록을 찾을 수 없습니다.'})
    



@login_required
def myprofile(request, username):
    if not request.session.get('password_verified'):
        return redirect('mypage:verify_password', username=username)

    User = get_user_model()
    user = get_object_or_404(User, username=username)

    if request.user != user:
        return redirect('mypage:mypage', username=request.user.username)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save(commit=False)

            password = form.cleaned_data.get('password1')
            if password:
                user.set_password(password)

            user.save()
            update_user_index(user)

            # backend 설정 후 로그인
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)

            request.session.pop('password_verified', None)

            return redirect('mypage:mypage', username=user.username)
    else:
        form = ProfileUpdateForm(instance=user)

    return render(request, 'myprofile.html', {
        'form': form,
        'me': user,
    })


@login_required
def verify_password(request, username):
    if request.user.username != username:
        return redirect('mypage:mypage', username=request.user.username)

    if request.method == 'POST':
        form = PasswordCheckForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                request.session['password_verified'] = True  # 세션에 인증 저장
                return redirect('mypage:myprofile', username=username)
            else:
                form.add_error('password', '비밀번호가 일치하지 않습니다.')
    else:
        form = PasswordCheckForm()

    return render(request, 'verify_password.html', {'form': form})