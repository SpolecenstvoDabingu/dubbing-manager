from django import template
from ..utils import manages_something as ms

register = template.Library()

@register.filter
def manages_something(user):
    return ms(user)