from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import Promise, PromiseVote
from .forms import PromiseForm
from datetime import timedelta
import json
from django.urls import reverse

# Create your views here.
@login_required
def promise(request):
    # promise_obj = Promise.objects.get(promise_name=promise_name)

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

        form = PromiseForm(post_data)

        # print("📌 POST 데이터:", request.POST)
        # print("📌 조합된 날짜:", start_date, end_date)
        # 모든 값이 입력되었는지 확인 후 날짜 조합
        if form.is_valid():
            # print("📌 form 유효, 저장 시도")
            saved_promise = form.save()
            # 저장 후 이동할 페이지
            # print("📌 저장 완료, redirect 시도")
            return redirect('promise:promise_vote', promise_id=saved_promise.id)

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
    return render(request, 'promise.html', context)

@login_required
def promise_vote(request, promise_id):
    promise = Promise.objects.get(id=promise_id)
    inclusive_end = promise.end_date + timedelta(days=1)

    if request.method == "POST":
    # 중복 투표 여부 확인
        has_voted = PromiseVote.objects.filter(username=request.user, promise=promise).exists()
        if has_voted:
            return redirect('promise:promise_result', promise_id=promise.id)

        selected = request.POST.get("selected_dates", "")
        selected_list = selected.split(",") if selected else []

        for date_str in selected_list:
            vote = PromiseVote(
                promise=promise,
                selected_date=date_str,
                username=request.user
            )
            vote.save()

    context = {
        'promise': promise,
        'start_date': promise.start_date.strftime('%Y-%m-%d'),
        'end_date': inclusive_end.strftime('%Y-%m-%d'),
    }

    return render(request, 'promise_vote.html', context)

    # GET요청인 경우 결과 화면을 보여줌

@login_required
def promise_result(request, promise_id):
    promise = Promise.objects.get(id=promise_id)
    
    if request.method == "POST":
        has_voted = PromiseVote.objects.filter(username=request.user, promise=promise).exists()
        if has_voted:
            return redirect('promise:promise_result', promise_id=promise.id)

        selected = request.POST.get("selected_dates", "")
        selected_list = selected.split(",") if selected else []

        # 선택된 날짜들 각각을 Vote 테이블에 저장
        for date_str in selected_list:
            vote = PromiseVote(
                promise=promise,
                selected_date=date_str,
                username=request.user
            )
            vote.save()

        return redirect('promise:promise_result', promise_id=promise.id)
        
    else:
        selected_list = PromiseVote.objects.filter(username=request.user, promise=promise).values_list('selected_date', flat=True)
        selected_list = [d.strftime('%Y-%m-%d') for d in selected_list]

    context = {
        'promise': promise, 
        # JS에서 사용 가능하게 json 변환
        'selected_dates': selected_list,
        'js_selected_dates': json.dumps(selected_list),
    }

    return render(request, 'promise_result.html', context)