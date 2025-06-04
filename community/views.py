from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from promise.models import Promise, PromiseVote
from mypage.models import CreateCommunity, FriendRequest
from .models import CommunityMember, CommunityInvite, Photo, PhotoComment, MoodVote
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
        create_user = community.create_user,
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

@login_required
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

@login_required
def update_image(request, community_id):
    community = CreateCommunity.objects.get(id=community_id)

    if request.method == "POST" and request.FILES.get("image"):
        community.community_image = request.FILES["image"]
        community.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, "message": "이미지가 없습니다."})

@login_required
def update_community_info(request, community_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            community = CreateCommunity.objects.get(id=community_id)
            community.community_name = data.get('community_name', community.community_name)
            community.community_intro = data.get('community_intro', community.community_intro)
            community.save()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
        
        return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def album_detail(request, community_id, album_name):
    # 해당 커뮤니티 id와 약속 이름에 해당하는 Promise 가져오기
    promise = Promise.objects.filter(community_id=community_id, promise_name=album_name).first()
    photos = Photo.objects.filter(promise=promise)

    # 내 기분
    user_mood = None
    if promise:
        mood_vote = MoodVote.objects.filter(promise=promise, user=request.user).first()
        if mood_vote:
            user_mood = mood_vote.mood

    # 전체 멤버 기분 리스트
    mood_votes = []
    if promise:
        votes = MoodVote.objects.filter(promise=promise).select_related('user')
        mood_votes = [{'username': vote.user.username, 'mood': vote.mood} for vote in votes]

    context = {
        'community_id': community_id,
        'promise': promise,
        'album_name': promise.promise_name,
        'photos': photos,
        'user_mood': user_mood,
        'mood_votes': mood_votes,
    }
    return render(request, 'album_detail.html', context)

@login_required
def upload_photo(request, community_id, album_name):
    if request.method == 'POST' and request.FILES.get('file'):
        promise = Promise.objects.filter(community_id=community_id, promise_name=album_name).first()
        image = request.FILES['file']
        photo = Photo.objects.create(image=image, promise=promise)
        
        return JsonResponse({
            'id': photo.id,
            'filename': photo.image.url
        })
    return JsonResponse({'error': 'invalid request'}, status=404)

@login_required
def mood_vote(request, community_id, album_name):
    data = json.loads(request.body)
    mood = data.get('mood')

    promise = Promise.objects.filter(community_id=community_id, promise_name=album_name).first()
    vote, created = MoodVote.objects.update_or_create(
        promise=promise, user=request.user, defaults={'mood': mood}
    )

    # 전체 커뮤니티 멤버별 기분 선택 결과
    votes = MoodVote.objects.filter(promise=promise).select_related('user')
    votes_list = [{'username': v.user.username, 'mood': v.mood} for v in votes]

    return JsonResponse({
        'user_mood': mood, 
        'votes': votes_list,
        'current_user': request.user.username})

@login_required
def photo_comment(request, community_id, album_name, photo_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            comment_text = data.get('text')

            photo = Photo.objects.get(id=photo_id)
            comment = PhotoComment.objects.create(photo=photo, author=request.user, text=comment_text)

            return JsonResponse({
                'success': True, 
                'comment': {
                    'author': request.user.username,
                    'text': comment.text,
                    'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        
    else: # GET
        try:
            photo = Photo.objects.get(id=photo_id)
            comments = PhotoComment.objects.filter(photo=photo).order_by('created_at')
            comment_list = [{
                'author': comment.author.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M")
            } for comment in comments]
            return JsonResponse({'success': True, 'comments': comment_list})
        except Photo.DoesNotExist:
            return JsonResponse({'success': False, 'message': '사진을 찾을 수 없습니다.'}, status=404)