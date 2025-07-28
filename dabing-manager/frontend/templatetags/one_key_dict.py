from django import template

register = template.Library()

@register.filter
def one_key_dict(value, key):
    return {key: value}