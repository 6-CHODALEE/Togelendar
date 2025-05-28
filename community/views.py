from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from promise.models import Promise, PromiseVote
from mypage.models import CreateCommunity, FriendRequest, CommunityMember, CommunityInvite
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import json
import logging

# Create your views here.
@login_required
def community_detail(request, community_id):
    community = CreateCommunity.objects.get(id=community_id)
    promises = Promise.objects.all()

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
        friend_users.append({
            'username': friend.username,
            'email': friend.email,
            'is_member': is_member,
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

# def add_member_ajax(request, community_id):
#     logger = logging.getLogger(__name__)
#     User = get_user_model()
    
#     try:
#         data = json.loads(request.body)
#         community_id = data.get('community_id')
#         username = data.get('username')

#         # 커뮤니티, 유저 찾기
#         community = CreateCommunity.objects.get(id=community_id)
#         user_to_add = User.objects.get(username=username)

#         # 이미 멤버인지 확인
#         if CommunityMember.objects.filter(
#                 community_name = community.community_name,
#                 create_user = community.create_user,
#                 member = username
#             ).exists():

#             return JsonResponse({'success': False, 'error': '이미 멤버입니다.'})

#         # 멤버 추가
#         CommunityMember.objects.create(
#             community_name = community.community_name,
#             create_user = community.create_user,
#             member = user_to_add.username
#         )

#         return JsonResponse({'success': True})

#     except Exception as e:
#         logger.error(f"[add_member_ajax] 오류 발생: {e}")
#         return JsonResponse({'suceess': False, 'error': str(e)})

def invite_member_ajax(request, community_id):
    data = json.loads(request.body)
    to_username = data.get('username')
    to_user = get_user_model().objects.get(username=to_username)
    community = CreateCommunity.objects.get(id=community_id)

    # 이미 보냈는지 확인
    existing = CommunityInvite.objects.filter(community=community, to_user=to_user)
    if existing.exists():
        return JsonResponse({'success': False, 'message': '이미 초대 보냄'})

    CommunityInvite.objects.create(
        community=community,
        from_user=request.user,
        to_user=to_user
    )

    return JsonResponse({'success': True})