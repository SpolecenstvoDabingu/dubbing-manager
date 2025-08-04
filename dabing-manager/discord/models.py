from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver

# Create your models here.
class DiscordUser(models.Model):
    user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, blank=True, null=True)
    discord_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    notification = models.BooleanField(default=False)
    avatar = models.URLField(max_length=512)

    @property
    def get_notification_data(self) -> dict:
        return {
            "id": self.discord_id,
            "notification": self.notification,
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

User.add_to_class("discord_display_name", discord_display_name)
User.add_to_class("discord_get_avatar", discord_get_avatar)

@receiver(post_delete, sender=DiscordUser)
def delete_related_user(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()