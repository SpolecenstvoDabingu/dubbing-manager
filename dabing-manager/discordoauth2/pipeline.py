from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from social_django.models import UserSocialAuth
from social_core.exceptions import AuthForbidden
from discord.models import DiscordUser

User = get_user_model()

def check_discord_whitelist(strategy, details, backend, uid, *args, **kwargs):
    """
    Only allow login if Discord user is whitelisted (is_member=True)
    """
    if backend.name != 'discord':
        return
    d_user = DiscordUser.objects.filter(discord_id=uid, is_member=True)
    if not d_user.exists():
        # Redirect to 'not_allowed' page if not whitelisted
        return redirect(reverse("not_allowed"))


def create_user_if_not_exists(strategy, details, backend, uid, user=None, *args, **kwargs):
    """
    Create a Django user if it does not exist.
    If the DiscordUser is already linked to a user, return that user.
    """
    if backend.name != 'discord':
        return

    # If a user is already passed (logged in), just return it
    if user:
        return {'user': user}

    discord_id = uid
    discord_user_qs = DiscordUser.objects.filter(discord_id=discord_id, is_member=True).first()
    if discord_user_qs is None:
        return redirect(reverse("not_allowed"))

    # If this DiscordUser is already linked to a Django user, use that
    if discord_user_qs.user:
        return {'user': discord_user_qs.user}

    # Create a new Django user
    discord_discriminator = details.get('username') or details.get('discriminator')
    if discord_discriminator:
        django_username = f"{discord_discriminator}_{discord_id}"
    else:
        django_username = f"discord_{discord_id}"

    user, created = User.objects.get_or_create(username=django_username)

    # Link DiscordUser to this Django user
    discord_user_qs.user = user
    discord_user_qs.save()

    return {'user': user}


def associate_discord_user(strategy, uid, user=None, backend=None, *args, **kwargs):
    """
    Associate the Discord account with a user.
    If the Discord account is already linked to another user, use that user.
    """
    if not backend or backend.name != 'discord':
        return

    # Check if this Discord account is already linked
    social_qs = UserSocialAuth.objects.filter(provider='discord', uid=uid)
    if social_qs.exists():
        return {'user': social_qs.first().user}

    # If not linked, associate with current user
    if user:
        UserSocialAuth.objects.create(user=user, provider='discord', uid=uid)
        return {'user': user}
