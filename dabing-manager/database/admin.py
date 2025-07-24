from django.contrib import admin
from .models import UserProfile, Dubbing, Character, Episode, Scene, UserCharacterStable, UserCharacterTemporary

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Dubbing)
admin.site.register(Character)
admin.site.register(Episode)
admin.site.register(Scene)
admin.site.register(UserCharacterStable)
admin.site.register(UserCharacterTemporary)
