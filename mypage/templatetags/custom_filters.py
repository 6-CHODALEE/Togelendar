from django import template

register = template.Library()

@register.filter
def get_item(obj, key):
    """
    딕셔너리: obj.get(key)
    리스트/튜플: obj[int(key)]
    """
    try:
        # 딕셔너리인 경우
        if hasattr(obj, 'get'):
            return obj.get(key)
        # 아니면 시퀀스 인덱싱
        return obj[int(key)]
    except Exception:
        return ''