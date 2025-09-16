from django import template
from ..utils import manages_something as ms, manages_this as mt

register = template.Library()

@register.filter
def manages_this(user, dubbing):
    from database.models import Dubbing
    if isinstance(dubbing, Dubbing):
        return mt(user, dubbing)
    if isinstance(dubbing, int):
        dub = Dubbing.objects.filter(id=dubbing)
        return mt(user, dub.first()) if dub.exists() else False
    return False