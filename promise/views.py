from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import Promise, PromiseVote, PromiseResult
from .forms import PromiseForm
from datetime import datetime, timedelta
import json
from django.urls import reverse
from community.models import CreateCommunity, CommunityMember
from collections import Counter
from user_account.models import User
from django.shortcuts import get_object_or_404
from collections import defaultdict


# Create your views here.
@login_required
def create_promise(request, community_id):
    community = CreateCommunity.objects.get(id=community_id)

    current_year = datetime.now().year
    
    years = list(range(current_year, current_year + 6))
    months = list(range(1,13))
    days = list(range(1, 32))

    if request.method == "POST":

        # 날짜 드롭다운 값 수집
        sy = request.POST.get("start-year", "")
        sm = request.POST.get("start-month", "")
        sd = request.POST.get("start-day", "")
        ey = request.POST.get("end-year", "")
        em = request.POST.get("end-month", "")
        ed = request.POST.get("end-day", "")

        start_date = f"{sy}-{sm.zfill(2)}-{sd.zfill(2)}"
        end_date = f"{ey}-{em.zfill(2)}-{ed.zfill(2)}"

        # 복합 POST 데이터 만들기
        post_data = request.POST.copy()
        post_data['start_date'] = start_date
        post_data['end_date'] = end_date
        post_data['promise_name'] = request.POST.get('promise_name', '')

        form = PromiseForm(post_data)

        # 모든 값이 입력되었는지 확인 후 날짜 조합
        if form.is_valid():
            promise = form.save(commit=False)
            promise.community = community
            promise.promise_creator = request.user.username
            promise.save()

            # 저장 후 이동할 페이지
            return redirect('community:promise:promise_vote', community_id=community.id, promise_id=promise.id)

    else:
        form = PromiseForm()
        # print("form 오류")

    # GET 요청일 경우 템플릿 렌더링
    context = {
        'form': form,
        'years': years,
        'months': months,
        'days': days
    }
    return render(request, 'create_promise.html', context)

@login_required
def promise_vote(request, community_id, promise_id):
    community = CreateCommunity.objects.get(id=community_id)
    promise = Promise.objects.get(id=promise_id, community=community)
 
    inclusive_end = promise.end_date + timedelta(days=1)

    if request.method == "POST":
    # 중복 투표 여부 확인
        has_voted = PromiseVote.objects.filter(username=request.user, promise=promise).exists()
        if has_voted:
            return redirect('community:promise:promise_result', community_id=community.id, promise_id=promise.id)

        selected = request.POST.get("selected_dates", "")
        selected_list = selected.split(",") if selected else []

        for date_str in selected_list:
            vote = PromiseVote(
                promise = promise,
                promise_name=promise.promise_name,
                selected_date=date_str,
                username=request.user
            )
            vote.save()
        return redirect('community:promise:promise_result', community_id=community.id, promise_id=promise.id)

    context = {
        'promise': promise,
        'community': community,
        'start_date': promise.start_date.strftime('%Y-%m-%d'),
        'end_date': inclusive_end.strftime('%Y-%m-%d'),
    }

    return render(request, 'promise_vote.html', context)

    # GET요청인 경우 결과 화면을 보여줌


@login_required
def promise_result(request, community_id, promise_id):

    community = get_object_or_404(CreateCommunity, id=community_id)
    promise = get_object_or_404(Promise, id=promise_id, community=community)

    votes = PromiseVote.objects.filter(promise=promise)
    vote_counter = Counter(vote.selected_date.strftime('%Y-%m-%d') for vote in votes)

    if request.method == "POST":
        has_voted = PromiseVote.objects.filter(username=request.user, promise=promise).exists()
        if has_voted:
            return redirect('community:promise:promise_result', community_id=community.id, promise_id=promise.id)

        selected = request.POST.get("selected_dates", "")
        selected_list = selected.split(",") if selected else []

        for date_str in selected_list:
            vote = PromiseVote(
                promise=promise,
                selected_date=date_str,
                username=request.user
            )
            vote.save()

        return redirect('community:promise:promise_result', community_id=community.id, promise_id=promise.id)

    else:
        selected_list = PromiseVote.objects.filter(username=request.user, promise=promise).values_list('selected_date', flat=True)
        selected_list = [d.strftime('%Y-%m-%d') for d in selected_list]

    total_members = CommunityMember.objects.filter(
        community_name=community.community_name,
        create_user=community.create_user
    ).count()
    responded_members = PromiseVote.objects.filter(promise=promise).values('username').distinct().count()
    all_voted = (responded_members == total_members)

    if all_voted and not PromiseResult.objects.filter(promise=promise).exists():
        if vote_counter:
            max_votes = max(vote_counter.values())
            top_dates = sorted([
                datetime.strptime(date_str, '%Y-%m-%d').date()
                for date_str, count in vote_counter.items() if count == max_votes
            ])

            ranges = []
            group = [top_dates[0]]

            for i in range(1, len(top_dates)):
                if (top_dates[i] - top_dates[i - 1]).days == 1:
                    group.append(top_dates[i])
                else:
                    ranges.append(group)
                    group = [top_dates[i]]
            ranges.append(group)

            for date_group in ranges:
                PromiseResult.objects.create(
                    promise=promise,
                    promise_name=promise.promise_name,
                    promise_creator=promise.promise_creator,
                    start_date=date_group[0],
                    end_date=date_group[-1],
                    center_latitude=0,
                    center_longitude=0
                )

    date_votes = [
        {
            "date": date,
            "count": count,
            "intensity": round(count / total_members, 2) if total_members > 0 else 0
        }
        for date, count in vote_counter.items()
    ]

    selected_type = request.GET.get('type', 'all')
    # 중복 제거 - 딱 한 번만 호출
    promise_result = PromiseResult.objects.filter(promise=promise).first()

    if not promise_result:
        center_latitude = 0
        center_longitude = 0
        places = []
        places_json = json.dumps([])
        selected_type = 'all'
    else:
        center_latitude = promise_result.center_latitude
        center_longitude = promise_result.center_longitude

        places_raw = promise_result.places_json
        if isinstance(places_raw, str):
            all_places = json.loads(places_raw)
        else:
            all_places = places_raw

        if selected_type == 'all':
            places = all_places
        else:
            places = [p for p in all_places if p.get('type') == selected_type]

        places_json = json.dumps(places)

    # ✅ is_location_decided 계산 (중복 제거 후)
    is_location_decided = (
        promise_result is not None and
        (promise_result.center_latitude != 0 or promise_result.center_longitude != 0)
    )

    voted_usernames = PromiseVote.objects.filter(promise=promise).values_list('username', flat=True).distinct()
    user_locations = User.objects.filter(username__in=voted_usernames).values('username', 'latitude', 'longitude')
    user_locations_list = list(user_locations)

    context = {
        'promise': promise,
        'community': community,
        'selected_dates': selected_list,
        'js_selected_dates': json.dumps(selected_list),
        'all_vote_data': json.dumps(date_votes),
        'total_members': total_members,
        'all_voted': all_voted,
        'center_latitude': center_latitude,
        'center_longitude': center_longitude,
        'user_locations': json.dumps(user_locations_list),
        'promise_result': promise_result,
        'places': places,
        'places_json': places_json,
        'selected_type': selected_type,
        'is_location_decided': is_location_decided,

    }

    return render(request, 'promise_result.html', context)

def no_place_promise(request, community_id):
    grouped_promises = defaultdict(list)

    results = PromiseResult.objects.filter(
        promise__community_id=community_id,
        center_latitude=0
    )

    for result in results:
        grouped_promises[result.promise].append(result)

    context = {
        'grouped_promises': grouped_promises.items(),  # (Promise 객체, [PromiseResult...])
        'community_id': community_id,
    }
    return render(request, 'no_place_promise.html', context)


from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Promise

@require_POST
def delete_promise(request, community_id, promise_id):
    promise = get_object_or_404(Promise, id=promise_id, community_id=community_id)

    # 선택적으로 작성자만 삭제하도록 제한하려면 아래 코드도 사용 가능
    if promise.promise_creator != request.user.username:
        return HttpResponseForbidden("삭제 권한이 없습니다.")

    promise.delete()
    return JsonResponse({'success': True})
