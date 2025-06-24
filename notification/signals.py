from django.db.models.signals import post_save
from django.dispatch import receiver
from community.models import CommunityMember
from notification.models import Notification
from user_account.models import User
from mypage.models import CreateCommunity
from promise.models import Promise, PromiseVote, PromiseResult
from community.models import PhotoComment


@receiver(post_save, sender=CommunityMember)
def notify_new_member(sender, instance, created, **kwargs):
    if created:
        community = instance.community_name
        new_member_username = instance.member
        inviter_username = instance.create_user

        # 해당 커뮤니티에 속해있는 기존 멤버들 가져오기(신규 멤버 제외)
        existing_members = CommunityMember.objects.filter(community_name=community).exclude(member=new_member_username)

        for member in existing_members:
            if member.member == inviter_username:
                continue # 초대한 사람은 제외
            
            try:
                user = User.objects.get(username=member.member)
                Notification.objects.create(
                    user=user,
                    notification_type='new_member',
                    message=f'👤 <strong>{new_member_username}</strong>님이 <strong>{community.community_name}</strong>에 새로 합류했어요!',
                    url=f'/community/{community.id}',
                    community=community
                )
            except User.DoesNotExist:
                continue
            
@receiver(post_save, sender=Promise)
def notify_promise_create(sender, instance, created, **kwargs):
    if created:
        # 약속이 생성되면, 해당 커뮤니티의 멤버 전원에게 알림 전송
        members = CommunityMember.objects.filter(community_name=instance.community)
        community = instance.community

        for member in members:
            try:
                user = User.objects.get(username=member.member)
                Notification.objects.create(
                    user=user,
                    notification_type='new_promise',
                    message=f'📅 <strong>{community.community_name}</strong>에 <strong>{instance.promise_name}</strong> 약속이 등록되었어요!',
                    url=f'/community/{community.id}/promise/{instance.id}/vote/',
                    promise=instance,
                    community=instance.community
                )
            except User.DoesNotExist:
                continue

@receiver(post_save, sender=PromiseVote)
def notify_vote_completed(sender, instance, created, **kwargs):
    if not created:
        return # 새로 생성된게 아니면 무시
    
    promise = instance.promise
    community = promise.community

    # 해당 커뮤니티의 전체 멤버 수
    community_members = CommunityMember.objects.filter(community_name=community)
    total_member_count = community_members.count()

    # 중복 없이 실제 투표한 유저 수
    voted_user_ids = (PromiseVote.objects.filter(promise=promise).values_list('username', flat=True).distinct())

    if len(voted_user_ids) == total_member_count:
        # 이미 알림이 전송된 적 있는지 확인(중복 방지)
        if Notification.objects.filter(notification_type='vote_complete', promise=promise)/exists():
            return

        for member in community_members:
            try:
                user = User.objects.get(username=member.member)
                Notification.objects.create(
                    user=user,
                    notification_type='vote_complete',
                    message=f'🗳️ <strong>{community.community_name}</strong>의 <strong>{promise.promise_name}</strong> 약속 투표를 완료했어요!',
                    url=f'/community/{community.id}/promise/{promise.id}/result/',
                    community=community,
                    promise=promise
                )
            except User.DoesNotExist:
                continue

@receiver(post_save, sender=PromiseResult)
def notify_place_selected(sender, instance, created, **kwargs):
    if not created:
        return
    
    promise = instance.promise
    community = promise.community
    members = CommunityMember.objects.filter(community_name=community)

    # 중복 알림 방지
    if Notification.objects.filter(notification_type='place_selected', promise=promise).exists():
        return

    for member in members:
        try:
            user = User.objects.get(username=member.member)
            Notification.objects.create(
                user=user,
                notification_type='place_selected',
                message=f'📍 <strong>{community.community_name}</strong>의 <strong>{promise.promise_name}</strong> 약속 장소가 정해졌어요!',
                url=f'/community/{community.id}/promise/{promise.id}/result/',
                community=community,
                promise=promise
            )
        except User.DoesNotExist:
            continue

@receiver(post_save, sender=PhotoComment)
def notify_photo_comment(sender, instance, created, **kwargs):
    if not created:
        return

    photo = instance.photo
    uploader = photo.uploaded_by
    commenter = instance.user
    promise = photo.promise
    community = promise.community
    
    # 자기 사진에 자기 댓글은 알림 안보냄
    if uploader == commenter or uploader is None:
        return
    
    # 중복 알림 방지 (동일한 사진+댓글 내용은 1회만)
    if Notification.objects.filter(
        notification_type='photo_comment', 
        photo=photo, 
        user=uploader, 
        message__contains=instance.content[:10] # 간단한 내용 중복 체크
    ).exists():
        return

    Notification.objects.create(
        user=uploader,
        notification_type='photo_comment',
        message=f'💬 <strong>{community.community_name}</strong>의 <strong>{promise.promise_name}</strong> 앨범 사진에 댓글이 달렸어요!',
        url=f'/community/{community.id}/album/{promise.promise_name}/{photo.id}/comment/',
        community=community,
        promise=promise,
        photo=photo
    )