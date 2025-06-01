from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from promise.models import Promise, PromiseVote
from mypage.models import CreateCommunity, FriendRequest
from community.models import CommunityMember, CommunityInvite
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import json
import logging

# Create your views here.
@login_required
def community_detail(request, community_id):
    community = CreateCommunity.objects.get(id=community_id)
    promises = Promise.objects.filter(community=community)

    # 친구 리스트 생성
    friend_list = FriendRequest.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    )

    # 친구의 user정보 추출
    friend_users = []
    for fr in friend_list:
        friend = fr.to_user if fr.from_user == request.user else fr.from_user

        # 이미 멤버인지 체크
        is_member = CommunityMember.objects.filter(
            community_name = community.community_name,
            create_user = community.create_user,
            member = friend.username
        ).exists()

        # 초대 했는지 체크
        has_invite = CommunityInvite.objects.filter(
            community = community,
            to_user = friend,
            status = 'pending'
        ).exists()

        friend_users.append({
            'username': friend.username,
            'email': friend.email,
            'is_member': is_member,
            'has_invite': has_invite,
        })

    # 커뮤니티 멤버 가져오기
    members = CommunityMember.objects.filter(
        community_name = community.community_name,
        create_user = community.create_user
    )
    
    # 현재 유저가 투표한 약속 id들
    voted_ids = PromiseVote.objects.filter(username=request.user).values_list('promise_id', flat=True)
    
    context = {
        'community': community,
        'members': members,
        'promises': promises,
        'voted_ids': list(voted_ids),
        'friend_users': friend_users,
    }
    return render(request, 'community_detail.html', context)

def invite_member_ajax(request, community_id):
    data = json.loads(request.body)
    to_username = data.get('username')
    to_user = get_user_model().objects.get(username=to_username)
    community = CreateCommunity.objects.get(id=community_id)

    # 이미 보냈는지 확인
    existing = CommunityInvite.objects.filter(community=community, to_user=to_user).first()

    if existing:
        if existing.status == 'pending':
            return JsonResponse({'success': False, 'message': '이미 초대 보냄'})
        # 상대방이 초대를 거절한 경우 다시 초대
        else:
            existing.status = 'pending'
            existing.from_user = request.user
            existing.save()
            return JsonResponse({'success': True, 'message': '재초대 보냄'})

    # 기존 초대가 없으면 새로 생성
    CommunityInvite.objects.create(
        community=community,
        from_user=request.user,
        to_user=to_user
    )

    return JsonResponse({'success': True})