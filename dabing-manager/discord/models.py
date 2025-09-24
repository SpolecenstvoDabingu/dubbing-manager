from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.files.base import ContentFile
import requests

# Create your models here.
class DiscordUser(models.Model):
    user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, blank=True, null=True)
    discord_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    notification = models.BooleanField(default=False)

    # internal storage
    avatar_url = models.URLField(max_length=512, blank=True, null=True)   # only for reference
    avatar_image = models.ImageField(upload_to="avatars/", blank=True, null=True, editable=False)

    is_member = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        avatar = kwargs.pop("avatar", None)  # intercept virtual field
        super().__init__(*args, **kwargs)
        if avatar is not None:
            self.avatar = avatar  # goes through setter

    @property
    def avatar(self):
        """Return the local cached image URL if available, otherwise remote URL."""
        return self.avatar_image.url if self.avatar_image else "https://cdn.discordapp.com/embed/avatars/0.png"

    @avatar.setter
    def avatar(self, value):
        """
        Accepts either a URL or a File/Image object.
        Always saves into avatar_image.
        """
        if not value:
            self.avatar_url = None
            if self.avatar_image:
                self.avatar_image.delete(save=False)
            return

        # Case 1: string (URL)
        if isinstance(value, str):
            self.avatar_url = value
            try:
                response = requests.get(value, timeout=10)
                response.raise_for_status()
                ext = value.split("?")[0].split(".")[-1] or "png"
                filename = f"{self.discord_id}.{ext}"
                
                old_image_name = str(self.avatar_image.name) if self.avatar_image else None
                self.avatar_image.save(filename, ContentFile(response.content), save=False)
                if old_image_name and old_image_name != self.avatar_image.name:
                    storage = self.avatar_image.storage
                    if storage.exists(old_image_name):
                        storage.delete(old_image_name)
            except Exception as e:
                print(f"Failed to cache avatar for {self.discord_id}: {e}")

    @property
    def get_notification_data(self) -> dict:
        return {
            "id": self.discord_id,
            "notification": self.notification if self.is_member else False,
        }

    def __str__(self):
        return f"{self.display_name or self.name} ({self.discord_id})"
    
    @staticmethod
    def bulk_update_avatar(instances):
        for instance in instances:
            if instance.avatar_url is not None and len(instance.avatar_url) > 0:
                instance.avatar = instance.avatar_url
                instance.avatar_url = None
        return instances
    
    def save(self, *args, **kwargs):
        if self.avatar_url is not None and len(self.avatar_url) > 0:
            self.avatar = self.avatar_url
            self.avatar_url = None
        super().save(*args, **kwargs)
    

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