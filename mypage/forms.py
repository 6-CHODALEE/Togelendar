from .models import CreateCommunity
from django.forms import ModelForm



class CreateCommunityFrom(ModelForm):
    class Meta():
        model = CreateCommunity
        fields = ['community_name', 'community_intro', 'community_image']
