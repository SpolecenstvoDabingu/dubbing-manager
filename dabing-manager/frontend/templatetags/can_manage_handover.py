from django import template
from api.utils import can_manage_handover as cmh

register = template.Library()

@register.filter
def can_manage_handover(user, ch_user):
    return cmh(user, ch_user)