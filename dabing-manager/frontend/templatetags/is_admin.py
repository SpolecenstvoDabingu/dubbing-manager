from django import template
from ..utils import is_admin as ia

register = template.Library()

@register.filter
def is_admin(user):
    return ia(user)