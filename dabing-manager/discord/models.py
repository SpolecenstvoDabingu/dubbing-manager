from django.db import models

# Create your models here.
class DiscordUser(models.Model):
    discord_id = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=255)
    avatar = models.URLField(max_length=512)

    def __str__(self):
        return f"{self.display_name} ({self.discord_id})"