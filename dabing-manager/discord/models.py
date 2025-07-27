from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class DiscordUser(models.Model):
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
    if hasattr(self, "social_auth"):
        user_sauth = self.social_auth.filter(provider='discord').first()
        if user_sauth:
            d_user = DiscordUser.objects.get(discord_id=self.social_auth.filter(provider='discord').first().uid)
            if d_user:
                return d_user.display_name or d_user.name
    return self.username

User.add_to_class("discord_display_name", discord_display_name)