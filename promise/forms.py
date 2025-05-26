from django import forms
from .models import Promise

class PromiseForm(forms.ModelForm):
    class Meta:
        model = Promise
        fields = ['title', 'start_date', 'end_date']