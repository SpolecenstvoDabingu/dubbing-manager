from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.utils import timezone

# Create your models here.
class DiscordUser(models.Model):
    user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, blank=True, null=True)
    discord_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    notification = models.BooleanField(default=False)
    avatar = models.URLField(max_length=512)
    is_member = models.BooleanField(default=False)

    @property
    def get_notification_data(self) -> dict:
        return {
            "id": self.discord_id,
            "notification": self.notification if self.is_member else False,
        }

    def __str__(self):
        return f"{self.display_name or self.name} ({self.discord_id})"
    

@property
def discord_display_name(self):
    try:
        if hasattr(self, "social_auth"):
            user_sauth = self.social_auth.filter(provider='discord').first()
            if user_sauth:
                d_user = DiscordUser.objects.get(discord_id=self.social_auth.filter(provider='discord').first().uid)
                if d_user:
                    return d_user.display_name or d_user.name
    except:
        return None
    return self.username


@property
def discord_get_avatar(self):
    try:
        if hasattr(self, "social_auth"):
            user_sauth = self.social_auth.filter(provider='discord').first()
            if user_sauth:
                d_user = DiscordUser.objects.get(discord_id=self.social_auth.filter(provider='discord').first().uid)
                if d_user:
                    return d_user.avatar or "https://cdn.discordapp.com/embed/avatars/0.png"
    except:
        return None
    return "https://cdn.discordapp.com/embed/avatars/0.png"

@property
def discord_is_member(self):
    try:
        if hasattr(self, "social_auth"):
            user_sauth = self.social_auth.filter(provider='discord').first()
            if user_sauth:
                d_user = DiscordUser.objects.get(discord_id=self.social_auth.filter(provider='discord').first().uid)
                if d_user:
                    return d_user.is_member
    except:
        return False
    return False

User.add_to_class("discord_display_name", discord_display_name)
User.add_to_class("discord_get_avatar", discord_get_avatar)
User.add_to_class("discord_is_member", discord_is_member)

@receiver(post_save, sender=DiscordUser)
def handle_non_member(sender, instance, created, **kwargs):
    if not created and not instance.is_member and instance.user:
        # End all sessions for this user (force logout)
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if str(instance.user.pk) == str(data.get('_auth_user_id')):
                session.delete()