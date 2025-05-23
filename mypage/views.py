from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CreateCommunityFrom
# Create your views here.


@login_required
def mypage(request, username):
    
    me = request.user
    context = {
        'me':me
    }
    return render(request, 'mypage.html', context)


def createcommunity(request, username):
    if request.method == 'POST':
        form = CreateCommunityFrom(request.POST, request.FILES)
        if form.is_valid():
            communityinfo = form.save(commit=False)
            communityinfo.createuser = request.user.username
            communityinfo.save()
            return redirect('mypage:mypage', username=request.user.username)
    else:
        form = CreateCommunityFrom()

    context = {
        'form' : form,
        'username': username
    }
    return render(request, 'createcommunity.html', context)
