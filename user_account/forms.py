from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django import forms

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'profile_image', 'postcode', 'address']
        labels = {
            'username': '아이디',
            'email': '이메일',
            'profile_image': '프로필 이미지',
            'postcode': '우편번호',
            'address': '주소',
        }

        

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': '아이디를 입력하세요',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '비밀번호를 입력하세요',
            'class': 'form-control'
        })
    )