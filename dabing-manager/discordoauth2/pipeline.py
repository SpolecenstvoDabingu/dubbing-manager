from social_core.exceptions import AuthForbidden
from discord.models import DiscordUser
from django.contrib.auth import get_user_model
from .exceptions import DiscordLoginNotAllowed
from django.shortcuts import redirect
from django.urls import reverse
User = get_user_model()

def check_discord_whitelist(strategy, details, backend, uid, *args, **kwargs):
    if backend.name != 'discord':
        return
    if not DiscordUser.objects.filter(discord_id=uid).exists():
        return redirect(reverse("not_allowed"))


def create_user_if_not_exists(strategy, details, backend, uid, user=None, *args, **kwargs):
    if user:
        return {'user': user}

    discord_id = uid
    discord_user_qs = DiscordUser.objects.filter(discord_id=discord_id)
    if not discord_user_qs.exists():
        return redirect(reverse("not_allowed"))

    discord_discriminator = details.get('username') or details.get('discriminator')

    if discord_discriminator:
        django_username = f"{discord_discriminator}_{discord_id}"
    else:
        django_username = f"discord_{discord_id}"

    user, created = User.objects.get_or_create(username=django_username)

    return {'user': user}