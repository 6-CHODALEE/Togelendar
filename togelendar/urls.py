"""
URL configuration for togelendar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.shortcuts import render, redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('index.urls')),
    path('api/notifications/', include('notification.urls')),
    path('account/', include('user_account.urls')),
    path('mypage/', include('mypage.urls')),
    path('community/', include('community.urls')),
    path('togelendar/', include('promiselocation.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




def custom_404_view(request, exception):
    if not request.user.is_authenticated:
        return redirect('account:login') 
    return render(request, '403.html', status=403)

handler404 = custom_404_view