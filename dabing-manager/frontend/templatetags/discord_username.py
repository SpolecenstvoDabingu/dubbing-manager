from django import template
from database.utils import get_user_discord_username

register = template.Library()

@register.filter
def discord_username(user):
    return get_user_discord_username(user)