from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required
def mypage(request, username):
    me = request.user
    context = {
        'me':me
    }
    return render(request, 'mypage.html', context)

