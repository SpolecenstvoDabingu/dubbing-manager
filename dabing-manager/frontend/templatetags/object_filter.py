from django import template

register = template.Library()

@register.filter
def object_filter(queryset, filter_dict):
    if isinstance(filter_dict, dict):
        return queryset.filter(**filter_dict)
    return queryset.all()