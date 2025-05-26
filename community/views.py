from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def community(request):
    return render(request, 'community.html')