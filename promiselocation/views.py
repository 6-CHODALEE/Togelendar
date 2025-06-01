from django.shortcuts import render

# Create your views here.
def location(request, community_id, promise_id):
    return render(request, 'location.html')