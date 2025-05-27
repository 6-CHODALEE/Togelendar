from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from promise.models import Promise, PromiseVote

# Create your views here.
@login_required
def community(request):
    promises = Promise.objects.all()

    # 현재 유저가 투표한 약속 id들
    voted_ids = PromiseVote.objects.filter(username=request.user).values_list('promise_id', flat=True)
    
    context = {
        'promises': promises,
        'voted_ids': list(voted_ids),
    }
    return render(request, 'community.html', context)