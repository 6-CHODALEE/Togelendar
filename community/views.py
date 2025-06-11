from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from promise.models import Promise, PromiseVote
from mypage.models import CreateCommunity, FriendRequest
from .models import CommunityMember, CommunityInvite, Photo, PhotoComment, MoodVote
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth import get_user_model
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Photo
from django.http import JsonResponse, Http404

# Create your views here.
@login_required
def community_detail(request, community_id):
    community = CreateCommunity.objects.get(id=community_id)
    promises = Promise.objects.filter(community=community)

    # 앨범 대표사진
    main_photos = {}
    for promise in promises:
        main_photo = promise.photo_set.filter(is_main=True).first()
        if main_photo:
            main_photos[promise.id] = main_photo

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

    member_users = []
    for m in members:
        user = m.member
        member_users.append({
            'username': user.username,
            'profile_image': user.profile_image.url if user.profile_image else None
        })
    
    # 현재 유저가 투표한 약속 id들
    voted_ids = PromiseVote.objects.filter(username=request.user).values_list('promise_id', flat=True)

    context = {
        'community': community,
        'members': members,
        'member_users': member_users,
        'promises': promises,
        'voted_ids': list(voted_ids),
        'friend_users': friend_users,
        'main_photos': main_photos,
        'username': request.user.username,
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
    community = CreateCommunity.objects.get(id=community_id)
    promise = Promise.objects.get(community_id=community_id, promise_name=album_name)
    photos = Photo.objects.filter(promise=promise)
    main_photo = photos.filter(is_main=True).first()

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
        'community': community,
        'community_id': community_id,
        'promise': promise,
        'album_name': promise.promise_name,
        'photos': photos,
        'user_mood': user_mood,
        'mood_votes': mood_votes,
        'main_photo': main_photo,
    }
    return render(request, 'album_detail.html', context)

@login_required
def upload_photo(request, community_id, album_name):
    if request.method == 'POST' and request.FILES.get('file'):
        promise = Promise.objects.filter(community_id=community_id, promise_name=album_name).first()
        if not promise:
            return JsonResponse({'error': '해당 약속을 찾을 수 없습니다.'}, status=404)

        image = request.FILES['file']
        photo = Photo.objects.create(
            image=image,
            promise=promise,
            uploaded_by=request.user  # ✅ 업로드한 사용자 설정
        )

        return JsonResponse({
            'id': photo.id,
            'filename': photo.image.url
        })

    return JsonResponse({'error': 'invalid request'}, status=400)

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
    photo = Photo.objects.get(id=photo_id)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                comment_content = data.get('content')

                comment = PhotoComment.objects.create(photo=photo, user=request.user, content=comment_content)

                return JsonResponse({
                    'success': True, 
                    'comment': {
                        'id': comment.id,  # ✅ 댓글 ID 포함
                        'user': request.user.username,
                        'content': comment.content,
                        'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                })
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)}, status=400)

        elif request.method == "GET":
            comments = PhotoComment.objects.filter(photo=photo).select_related('user').order_by('created_at')
            comment_list = [{
                'id': comment.id,
                'user': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M")
            } for comment in comments]

            return JsonResponse({'success': True, 'comments': comment_list})

    # HTML 전체 렌더링용 context
    context = {
        'community_id': community_id,
        'album_name': album_name,
        'photos': Photo.objects.filter(promise__community_id=community_id, promise__promise_name=album_name),
        'selected_photo': photo,
        'comments': PhotoComment.objects.filter(photo=photo).order_by('created_at'),
        'user_mood': get_user_mood(user=request.user, album_name=album_name),
        'mood_votes': get_mood_votes(album_name=album_name),
    }

    return render(request, 'album_detail.html', context)

def get_user_mood(user, album_name):
    try:
        vote = MoodVote.objects.get(user=user, promise=promise)
        return vote.mood
    except (Promise.DoesNotExist, MoodVote.DoesNotExist):
        return None

def get_mood_votes(album_name):
    try:
        votes = MoodVote.objects.filter(promise=promise).select_related('user')
        return [{'username': vote.user.username, 'mood': vote.mood} for vote in votes]
    except Promise.DoesNotExist:
        return []

@login_required
def album_main_photo(request, community_id, album_name, photo_id):
    if request.method != "POST":
        return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'}, status=405)

    try:
        promise = Promise.objects.get(community__id=community_id, promise_name=album_name)
        selected_photo = Photo.objects.get(id=photo_id, promise=promise)

        # 기존 대표사진 false로 초기화
        Photo.objects.filter(promise=promise).update(is_main=False)

        # 현재 사진을 대표사진으로
        selected_photo.is_main = True
        selected_photo.save()
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'sueccess': False, 'message': str(e)}, status=500)

@login_required
def delete_community(request, community_id):
    community = get_object_or_404(CreateCommunity, id=community_id)

    if request.method == 'POST':
        if request.user.username == community.create_user:  # 보안 check
            community.delete()  # 관련된 모든 데이터 CASCADE 삭제
            return redirect('mypage:mypage', username=request.user.username)  # 삭제 후 이동할 페이지
        else:
            return HttpResponseForbidden("삭제 권한이 없습니다.")




@require_POST
def delete_photo(request, community_id, album_name, photo_id):
    photo = get_object_or_404(Photo, id=photo_id)

    # 추가 검증 (옵션): 해당 photo가 요청한 community/album에 속하는지
    if photo.promise.community.id != community_id or photo.promise.promise_name != album_name:
        raise Http404("해당 앨범의 사진이 아닙니다.")

    photo.delete()
    return JsonResponse({'status': 'success'})


from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden, Http404
from .models import PhotoComment

@require_POST
@login_required
def comment_delete(request, community_id, album_name, photo_id, comment_id):
    try:
        comment = PhotoComment.objects.get(id=comment_id, photo_id=photo_id)

        # 작성자만 삭제 가능
        if comment.user != request.user:
            return HttpResponseForbidden("권한이 없습니다.")

        comment.delete()
        return JsonResponse({'success': True})

    except PhotoComment.DoesNotExist:
        raise Http404("댓글을 찾을 수 없습니다.")


@require_POST
@login_required
def comment_edit(request, community_id, album_name, photo_id, comment_id):
    try:
        comment = PhotoComment.objects.get(id=comment_id, photo_id=photo_id)

        # 작성자만 수정 가능
        if comment.user != request.user:
            return HttpResponseForbidden("권한이 없습니다.")

        data = json.loads(request.body)
        new_content = data.get('content', '').strip()

        if new_content:
            comment.content = new_content
            comment.save()
            return JsonResponse({
                'success': True,
                'updated_content': comment.content,
                'updated_at': comment.created_at.strftime("%Y-%m-%d %H:%M")
            })
        else:
            return JsonResponse({'success': False, 'message': '내용이 비어 있습니다.'}, status=400)

    except PhotoComment.DoesNotExist:
        raise Http404("댓글을 찾을 수 없습니다.")