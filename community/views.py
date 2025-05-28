from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from promise.models import Promise, PromiseVote
from mypage.models import CreateCommunity, FriendRequest, CommunityMember
from django.db.models import Q

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

    # 현재 유저가 투표한 약속 id들
    voted_ids = PromiseVote.objects.filter(username=request.user).values_list('promise_id', flat=True)
    
    context = {
        'community': community,
        'promises': promises,
        'voted_ids': list(voted_ids),
        'friend_users': friend_users,
    }
    return render(request, 'community_detail.html', context)