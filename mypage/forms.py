from .models import CreateCommunity
from django.forms import ModelForm
from django import forms
from .models import User
from django.contrib.auth import get_user_model


class CreateCommunityFrom(ModelForm):
    class Meta():
        model = CreateCommunity
        fields = ['community_name', 'community_intro', 'community_image']

    def clean_community_name(self):
        name = self.cleaned_data['community_name']
        if CreateCommunity.objects.filter(community_name=name).exists():
            raise forms.ValidationError("같은 이름의 커뮤니티가 존재합니다. \n다른 이름을 작성해주세요.")
        return name


User = get_user_model()

class ProfileUpdateForm(forms.ModelForm):
    password1 = forms.CharField(label='새 비밀번호', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='비밀번호 확인', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'profile_image', 'postcode', 'address']
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly'}),  # 🔒 이름은 읽기 전용
        }

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("password1")
        pw2 = cleaned_data.get("password2")
        if pw1 or pw2:
            if pw1 != pw2:
                raise forms.ValidationError("비밀번호가 일치하지 않습니다.")


class PasswordCheckForm(forms.Form):
    password = forms.CharField(
        label='비밀번호 확인',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )