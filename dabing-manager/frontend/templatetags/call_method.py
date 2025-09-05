from django import template

register = template.Library()

@register.simple_tag
def call_method(obj, method_name, **kwargs):
    """
    Call a method on an object with keyword arguments from the template.
    Usage:
        {% call_method obj "method_name" key1="val" key2="val" %}
    """
    method = getattr(obj, method_name, None)
    if callable(method):
        return method(**kwargs)
    return ""
