from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime

# Create your views here.
def promise(request):
    current_year = datetime.now().year
    
    years = list(range(current_year, current_year + 6))
    months = list(range(1,13))
    days = list(range(1, 32))
    context = {
        'years': years,
        'months': months,
        'days': days
    }
    return render(request, 'promise.html', context)
