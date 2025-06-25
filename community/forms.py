from django import forms
from .models import CommunityMemo

class CommunityMemoForm(forms.ModelForm):
    class Meta:
        model = CommunityMemo
        fields = ['content', 'is_done']
        widgets = {
            'content': forms.TextInput(attrs={'placeholder': '할 일을 입력하세요...'}),
        }