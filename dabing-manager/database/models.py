from django.db import models
from abc import abstractmethod
import os, json
from django.contrib.auth.models import User
from django.forms import ValidationError
from core.settings import NO_THUMBNAIL_URL
from .utils import HashedFilePath, one_week_from_now, get_user_discord_username, sanitize_markdown_links
from django.http import FileResponse, Http404
from django.utils.translation import pgettext
from django.utils import timezone

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    token = models.CharField(max_length=64, unique=True)

    class Meta:
        permissions = [
            ('is_admin', "User is server Admin"),
        ]

    def __str__(self) -> str:
        return f'{self.user.username} Profile'
    
    def get_custom_permissions(self) -> list:
        return [permission[0] for permission in self._meta.permissions]
    
    def regenerate_token(self) -> str:
        from core.utils import generate_unique_token
        self.token = generate_unique_token(UserProfile)
        self.save()
        return self.token
    

class Dubbing(models.Model):
    name = models.CharField(max_length=128, default="Dubbing Name", unique=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='dubbing', null=True, blank=True)

    description = models.TextField(max_length=1024, default="", blank=True)
    urls = models.TextField(max_length=1024, default="", blank=True)

    def __str__(self):
        return f"{self.name}"
    

    def save(self, ia=False):
        if not ia:
            self.description = sanitize_markdown_links(self.description)
            self.urls = sanitize_markdown_links(self.urls)
        
        super().save()
    
    
    @staticmethod
    def get_add_modal_fields_json():
        discord_users = User.objects.filter(social_auth__provider="discord").distinct()

        manager_options = [
            {"label": get_user_discord_username(user), "value": user.id}
            for user in discord_users
        ]

        fields = [
            {"type": "text", "label": pgettext('Dubbing name field label', 'frontend.database.models.dubbing.name'), "name": "name", "required": True},
            {"type": "textarea", "label": pgettext('Dubbing description field label', 'frontend.database.models.dubbing.description'), "name": "description"},
            {"type": "textarea", "label": pgettext('Dubbing urls field label', 'frontend.database.models.dubbing.urls'), "name": "urls"},
            {
                "type": "select",
                "label": pgettext('Dubbing manager field label', 'frontend.database.models.dubbing.manager'),
                "name": "manager",
                "options": manager_options
            },
        ]

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self):
        discord_users = User.objects.filter(social_auth__provider="discord").distinct()

        manager_options = [
            {"label": get_user_discord_username(user), "value": user.id}
            for user in discord_users
        ]

        fields = [
            {
                "type": "text",
                "label": pgettext('Dubbing name field label', 'frontend.database.models.dubbing.name'),
                "name": "name",
                "value": self.name,
                "required": True,
            },
            {
                "type": "textarea",
                "label": pgettext('Dubbing description field label', 'frontend.database.models.dubbing.description'),
                "name": "description",
                "value": self.description,
            },
            {
                "type": "textarea",
                "label": pgettext('Dubbing urls field label', 'frontend.database.models.dubbing.urls'),
                "name": "urls",
                "value": self.urls,
            },
            {
                "type": "select",
                "label": pgettext('Dubbing manager field label', 'frontend.database.models.dubbing.manager'),
                "name": "manager",
                "value": self.manager.id if self.manager else None,
                "options": manager_options,
            },
        ]

        return json.dumps(fields)

class Character(models.Model):
    dubbing = models.ForeignKey(Dubbing, on_delete=models.CASCADE, related_name="character_stable")
    name = models.CharField(max_length=128, default="Character Name")
    image = models.ImageField(max_length=512, upload_to=HashedFilePath("image", "images"), default=NO_THUMBNAIL_URL, blank=True, null=True)
    description = models.TextField(max_length=1024, default="", blank=True)

    def __str__(self):
        return f"{self.name}"
    
    def save(self, ia=False):
        if not ia:
            self.description = sanitize_markdown_links(self.description)
        
        super().save()
        
    @property
    def modify_character_data(self):
        return self.get_modify_modal_fields_json(dubbing=self.dubbing)
    
    @staticmethod
    def get_add_modal_fields_json(dubbing):
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
        ]

        fields = [
            {
                "type": "select",
                "label": pgettext('Episode field label', 'frontend.database.models.character.dubbing'),
                "name": "dubbing",
                "options": dubbing_options
            },
            {
                "type": "text",
                "label": pgettext('Character name field label', 'frontend.database.models.character.name'),
                "name": "name",
                "required": True,
            },
            {
                "type": "file",
                "label": pgettext('Character image field label', 'frontend.database.models.character.image'),
                "name": "image",
                "accept": "image/*"
            },
            {
                "type": "textarea",
                "label": pgettext('Character description field label', 'frontend.database.models.character.description'),
                "name": "description",
            },
        ]

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self, dubbing):
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
        ]

        fields = [
            {
                "type": "select",
                "label": pgettext('Episode field label', 'frontend.database.models.character.dubbing'),
                "name": "episode",
                "options": dubbing_options,
                "value": self.dubbing.id,
            },
            {
                "type": "text",
                "label": pgettext('Character name field label', 'frontend.database.models.character.name'),
                "name": "name",
                "required": True,
                "value": self.name,
            },
            {
                "type": "file",
                "label": pgettext('Character image field label', 'frontend.database.models.character.image'),
                "name": "image",
                "accept": "image/*"
            },
            {
                "type": "textarea",
                "label": pgettext('Character description field label', 'frontend.database.models.character.description'),
                "name": "description",
                "value": self.description,
            },
        ]

        return json.dumps(fields)

class Episode(models.Model):
    name = models.CharField(max_length=128, default="Episode Name")
    dubbing = models.ForeignKey(Dubbing, on_delete=models.CASCADE, related_name="episode")
    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(default=one_week_from_now)

    season = models.PositiveSmallIntegerField(default=1)
    episode = models.PositiveSmallIntegerField(default=1)

    script = models.FileField(max_length=512, upload_to=HashedFilePath("script", "scripts"))
    urls = models.TextField(max_length=1024, default="", blank=True)

    def get_se(self) -> str:
        return f"S{self.season:02d}E{self.episode:02d}"

    def __str__(self):
        return f"{self.dubbing} - {self.get_se()} - {self.name}"
    
    def save(self, ia=False):
        if not ia:
            self.urls = sanitize_markdown_links(self.urls)
        
        super().save()
    
    def get_script_download_response(self):
        if not self.script:
            raise Http404("Script file not found")

        file_path = self.script.path
        original_ext = os.path.splitext(self.script.name)[1]
        custom_filename = f"{self.__str__()}_script{original_ext}"

        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=custom_filename)
    
    @property
    def times_up(self) -> bool:
        return self.deadline < timezone.now()
    
    @property
    def is_manager(self, user) -> bool:
        return self.dubbing.manager == user
    
    @property
    def modify_episode_data(self):
        return self.get_modify_modal_fields_json()
    
    @staticmethod
    def get_add_modal_fields_json():
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
            for dubbing in Dubbing.objects.all()
        ]

        fields = [
            {"type": "text", "label": pgettext('Episode name field label', 'frontend.database.models.episode.name'), "name": "name", "required": True},
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.episode.dubbing'),
                "name": "dubbing",
                "options": dubbing_options
            },
            {"type": "datetime", "label": pgettext('Episode deadline field label', 'frontend.database.models.episode.deadline'), "name": "deadline", "value": one_week_from_now().strftime("%Y-%m-%dT%H:%M")},
            {"type": "number", "label": pgettext('Episode season field label', 'frontend.database.models.episode.season'), "name": "season", "value": 1},
            {"type": "number", "label": pgettext('Episode episode field label', 'frontend.database.models.episode.episode'), "name": "episode", "value": 1},
            {"type": "file", "label": pgettext('Episode script field label', 'frontend.database.models.episode.script'), "name": "script", "accept": ".pdf", "required": True},
            {"type": "textarea", "label": pgettext('Episode urls field label', 'frontend.database.models.episode.urls'), "name": "urls"},
        ]

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self):
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
            for dubbing in Dubbing.objects.all()
        ]

        fields = [
            {
                "type": "text",
                "label": pgettext('Episode name field label', 'frontend.database.models.episode.name'),
                "name": "name",
                "value": self.name,
                "required": True
            },
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.episode.dubbing'),
                "name": "dubbing",
                "options": dubbing_options,
                "value": self.dubbing.id
            },
            {
                "type": "datetime",
                "label": pgettext('Episode deadline field label', 'frontend.database.models.episode.deadline'),
                "name": "deadline",
                "value": self.deadline.strftime("%Y-%m-%dT%H:%M") if self.deadline else ""
            },
            {
                "type": "number",
                "label": pgettext('Episode season field label', 'frontend.database.models.episode.season'),
                "name": "season",
                "value": self.season
            },
            {
                "type": "number",
                "label": pgettext('Episode episode field label', 'frontend.database.models.episode.episode'),
                "name": "episode",
                "value": self.episode
            },
            {
                "type": "file",
                "label": pgettext('Episode script field label', 'frontend.database.models.episode.script'),
                "name": "script",
                "accept": ".pdf"
            },
            {
                "type": "textarea",
                "label": pgettext('Episode urls field label', 'frontend.database.models.episode.urls'),
                "name": "urls",
                "value": self.urls or ""
            },
        ]

        return json.dumps(fields)

class Scene(models.Model):
    name = models.CharField(max_length=128, default="Scene Name")
    dubbing = models.ForeignKey(Dubbing, on_delete=models.CASCADE, related_name="scene")
    created = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(default=one_week_from_now)

    script = models.FileField(max_length=512, upload_to=HashedFilePath("script", "scripts"))
    urls = models.TextField(max_length=1024, default="", blank=True)

    def __str__(self):
        return f"{self.dubbing} - {self.name}"
    
    @property
    def times_up(self) -> bool:
        return self.deadline < timezone.now()
    
    @property
    def is_manager(self, user) -> bool:
        return self.dubbing.manager == user
    
    @property
    def modify_scene_data(self):
        return self.get_modify_modal_fields_json()
    
    def save(self, ia=False):
        if not ia:
            self.urls = sanitize_markdown_links(self.urls)
        
        super().save()
    
    def get_script_download_response(self):
        if not self.script:
            raise Http404("Script file not found")

        file_path = self.script.path
        original_ext = os.path.splitext(self.script.name)[1]
        custom_filename = f"{self.__str__()}_script{original_ext}"

        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=custom_filename)
    
    @staticmethod
    def get_add_modal_fields_json():
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
            for dubbing in Dubbing.objects.all()
        ]

        fields = [
            {"type": "text", "label": pgettext('Scene name field label', 'frontend.database.models.scene.name'), "name": "name", "required": True},
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.scene.dubbing'),
                "name": "dubbing",
                "options": dubbing_options
            },
            {"type": "datetime", "label": pgettext('Scene deadline field label', 'frontend.database.models.scene.deadline'), "name": "deadline", "value": one_week_from_now().strftime("%Y-%m-%dT%H:%M")},
            {"type": "file", "label": pgettext('Scene script field label', 'frontend.database.models.scene.script'), "name": "script", "accept": ".pdf", "required": True},
            {"type": "textarea", "label": pgettext('Scene urls field label', 'frontend.database.models.scene.urls'), "name": "urls"},
        ]

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self):
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
            for dubbing in Dubbing.objects.all()
        ]

        fields = [
            {
                "type": "text",
                "label": pgettext('Scene name field label', 'frontend.database.models.scene.name'),
                "name": "name",
                "value": self.name,
                "required": True
            },
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.scene.dubbing'),
                "name": "dubbing",
                "options": dubbing_options,
                "value": self.dubbing.id
            },
            {
                "type": "datetime",
                "label": pgettext('Scene deadline field label', 'frontend.database.models.scene.deadline'),
                "name": "deadline",
                "value": self.deadline.strftime("%Y-%m-%dT%H:%M") if self.deadline else ""
            },
            {
                "type": "file",
                "label": pgettext('Scene script field label', 'frontend.database.models.scene.script'),
                "name": "script",
                "accept": ".pdf"
            },
            {
                "type": "textarea",
                "label": pgettext('Scene urls field label', 'frontend.database.models.scene.urls'),
                "name": "urls",
                "value": self.urls or ""
            },
        ]

        return json.dumps(fields)



class UserCharacterBase(models.Model):
    class Meta:
        abstract = True

    episode = models.ForeignKey(Episode, on_delete=models.SET_NULL, related_name='%(class)s', null=True, blank=True)
    scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, related_name='%(class)s', null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s')
    done = models.BooleanField(default=False)

    def clean(self):
        if bool(self.episode) == bool(self.scene):
            raise ValidationError("Exactly one of episode or scene must be set.")
        
    @property
    def notification_data(self):
        return {
            "e_s_name": self.episode.name if self.episode else self.scene.name,
            "dubbing_name": self.episode.dubbing.name if self.episode else self.scene.dubbing.name
        }
        
    @property
    def modify_character_data(self):
        return self.get_modify_modal_fields_json(episode=self.episode, scene=self.scene)
        
    @abstractmethod
    def get_modify_modal_fields_json(self, episode:Episode=None, scene:Scene=None):
        pass
        
class UserCharacterStable(UserCharacterBase):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='user')

    @property
    def dubbing(self):
        return self.character.dubbing
    
    @staticmethod
    def get_add_modal_fields_json(episode:Episode=None, scene:Scene=None):
        if episode is not None:
            character_options = [
                {"label": f"{i}", "value": i.id}
                for i in Character.objects.all()
                if episode.dubbing == i.dubbing
            ]
            episode_options = [
                {"label": f"{i}", "value": i.id}
                for i in Episode.objects.all()
                if episode == i
            ]
        if scene is not None:
            character_options = [
                {"label": f"{i}", "value": i.id}
                for i in Character.objects.all()
                if scene.dubbing == i.dubbing
            ]
            scene_options = [
                {"label": f"{i}", "value": i.id}
                for i in Scene.objects.all()
                if scene == i
            ]
        discord_users = User.objects.filter(social_auth__provider="discord").distinct()
        user_options = [
            {"label": get_user_discord_username(user), "value": user.id}
            for user in discord_users
        ]

        fields = []

        if episode is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Character field label', 'frontend.database.models.user_character.character'),
                "name": "character",
                "options": character_options
            })
            fields.append({
                "type": "select",
                "label": pgettext('Episode field label', 'frontend.database.models.user_character.episode'),
                "name": "episode",
                "options": episode_options
            })

        if scene is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Character field label', 'frontend.database.models.user_character.character'),
                "name": "character",
                "options": character_options
            })
            fields.append({
                "type": "select",
                "label": pgettext('Scene field label', 'frontend.database.models.user_character.scene'),
                "name": "scene",
                "options": scene_options
            })

        fields.append({
            "type": "select",
            "label": pgettext('User field label', 'frontend.database.models.user_character.user'),
            "name": "user",
            "options": user_options
        })

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self, episode:Episode=None, scene:Scene=None):
        if episode is not None:
            episode_options = [
                {"label": f"{i}", "value": i.id}
                for i in Episode.objects.all()
                if episode == i
            ]
        if scene is not None:
            scene_options = [
                {"label": f"{i}", "value": i.id}
                for i in Scene.objects.all()
                if scene == i
            ]
        discord_users = User.objects.filter(social_auth__provider="discord").distinct()
        user_options = [
            {"label": get_user_discord_username(user), "value": user.id}
            for user in discord_users
        ]

        fields = []

        if episode is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Episode field label', 'frontend.database.models.user_character.episode'),
                "name": "episode",
                "options": episode_options
            })

        if scene is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Scene field label', 'frontend.database.models.user_character.scene'),
                "name": "scene",
                "options": scene_options
            })

        fields.append({
            "type": "select",
            "label": pgettext('User field label', 'frontend.database.models.user_character.user'),
            "name": "user",
            "options": user_options
        })

        return json.dumps(fields)
    

class UserCharacterTemporary(UserCharacterBase):
    name = models.CharField(max_length=128, default="Character Name")
    image = models.ImageField(max_length=512, upload_to=HashedFilePath("image", "images"))
    description = models.TextField(max_length=1024, default="", blank=True)
    
    def save(self, ia=False):
        if not ia:
            self.description = sanitize_markdown_links(self.description)
        
        super().save()
    
    @staticmethod
    def get_add_modal_fields_json(episode:Episode=None, scene:Scene=None):
        if episode is not None:
            episode_options = [
                {"label": f"{i}", "value": i.id}
                for i in Episode.objects.all()
                if episode == i
            ]
        if scene is not None:
            scene_options = [
                {"label": f"{i}", "value": i.id}
                for i in Scene.objects.all()
                if scene == i
            ]
        discord_users = User.objects.filter(social_auth__provider="discord").distinct()
        user_options = [
            {"label": get_user_discord_username(user), "value": user.id}
            for user in discord_users
        ]

        fields = [
            {
                "type": "text",
                "label": pgettext('Character name field label', 'frontend.database.models.character.name'),
                "name": "name",
                "required": True,
            },
            {
                "type": "file",
                "label": pgettext('Character image field label', 'frontend.database.models.character.image'),
                "name": "image",
                "accept": "image/*"
            },
            {
                "type": "textarea",
                "label": pgettext('Character description field label', 'frontend.database.models.character.description'),
                "name": "description",
            },
        ]

        if episode is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Episode field label', 'frontend.database.models.user_character.episode'),
                "name": "episode",
                "options": episode_options
            })

        if scene is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Scene field label', 'frontend.database.models.user_character.scene'),
                "name": "scene",
                "options": scene_options
            })

        fields.append({
            "type": "select",
            "label": pgettext('User field label', 'frontend.database.models.user_character.user'),
            "name": "user",
            "options": user_options
        })

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self, episode:Episode=None, scene:Scene=None):
        if episode is not None:
            episode_options = [
                {"label": f"{i}", "value": i.id}
                for i in Episode.objects.all()
                if episode == i
            ]
        if scene is not None:
            scene_options = [
                {"label": f"{i}", "value": i.id}
                for i in Scene.objects.all()
                if scene == i
            ]
        discord_users = User.objects.filter(social_auth__provider="discord").distinct()
        user_options = [
            {"label": get_user_discord_username(user), "value": user.id}
            for user in discord_users
        ]

        fields = [
            {
                "type": "text",
                "label": pgettext('Character name field label', 'frontend.database.models.character.name'),
                "name": "name",
                "required": True,
                "value": self.name,
            },
            {
                "type": "file",
                "label": pgettext('Character image field label', 'frontend.database.models.character.image'),
                "name": "image",
                "accept": "image/*"
            },
            {
                "type": "textarea",
                "label": pgettext('Character description field label', 'frontend.database.models.character.description'),
                "name": "description",
                "value": self.description,
            },
        ]

        if episode is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Episode field label', 'frontend.database.models.user_character.episode'),
                "name": "episode",
                "options": episode_options
            })

        if scene is not None:
            fields.append({
                "type": "select",
                "label": pgettext('Scene field label', 'frontend.database.models.user_character.scene'),
                "name": "scene",
                "options": scene_options
            })

        fields.append({
            "type": "select",
            "label": pgettext('User field label', 'frontend.database.models.user_character.user'),
            "name": "user",
            "options": user_options
        })

        return json.dumps(fields)