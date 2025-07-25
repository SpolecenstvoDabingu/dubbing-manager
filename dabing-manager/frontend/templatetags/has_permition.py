from django import template

register = template.Library()

@register.filter
def has_permition(user, perm):
    if not user.is_authenticated:
        return False

    app_label, codename = perm.split('.', 1)

    return user.user_permissions.filter(
        codename=codename,
        content_type__app_label=app_label
    ).exists()