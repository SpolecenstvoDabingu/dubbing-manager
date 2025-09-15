from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, UserCharacterStable, Scene, Episode, Character, Dubbing
from core.utils import generate_unique_token
from django.core.files.storage import default_storage
from django.db.models.fields.files import FileField
from .utils import is_default_value

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, token=generate_unique_token(UserProfile))

@receiver(pre_save, sender=UserCharacterStable)
@receiver(pre_save, sender=Dubbing)
@receiver(pre_save, sender=Scene)
@receiver(pre_save, sender=Episode)
@receiver(pre_save, sender=Character)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        # New object, no old file to delete
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    for field in sender._meta.get_fields():
        if isinstance(field, FileField):
            old_file = getattr(old_instance, field.name)
            new_file = getattr(instance, field.name)
            if not old_file == new_file:
                if is_default_value(field, old_file):
                    continue

                if old_file and default_storage.exists(old_file.name):
                    default_storage.delete(old_file.name)

@receiver(post_delete, sender=UserCharacterStable)
@receiver(post_delete, sender=Dubbing)
@receiver(post_delete, sender=Scene)
@receiver(post_delete, sender=Episode)
@receiver(post_delete, sender=Character)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    for field in sender._meta.get_fields():
        if isinstance(field, FileField):
            file = getattr(instance, field.name)
            if file:
                if is_default_value(field, file):
                    continue
                
                if default_storage.exists(file.name):
                    default_storage.delete(file.name)