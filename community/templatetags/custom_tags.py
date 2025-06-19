import random
from django import template

register = template.Library()

@register.simple_tag
def random_album_image():
    choices = [
        'profile/diary_character.png',
        'profile/pink_diary_character.png',
        'profile/camera_character.png',
    ]
    return '/media/' + random.choice(choices)
