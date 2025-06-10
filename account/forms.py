from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django import forms

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email', 'profile_image', 'postcode', 'address']
        labels = {
            'username': '아이디',
            'email': '이메일',
            'profile_image': '프로필 이미지',
            'postcode': '우편번호',
            'address': '주소',
        }

        

class CustomAuthenticationForm(AuthenticationForm):
    pass