from django import template
from frontend.utils import to_utc_iso as tui

register = template.Library()

@register.filter
def to_utc_iso(dt, as_string="False"):
    as_string = as_string == "True"
    return tui(dt, as_string)