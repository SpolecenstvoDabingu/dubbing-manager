from django.db import models
from abc import abstractmethod
import os, json
from django.contrib.auth.models import User
from django.forms import ValidationError
from core.settings import NO_THUMBNAIL_URL
from operator import attrgetter
from .utils import HashedFilePath, today, one_week_from_now, three_days_from_now, one_week_from, three_days_from, get_user_discord_username, sanitize_markdown_links
from django.http import FileResponse, Http404
from django.utils.translation import pgettext
from django.utils import timezone
from datetime import datetime, time
from .utils import to_utc_iso

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

    cover = models.ImageField(max_length=512, upload_to=HashedFilePath("cover", "covers/dubbing"), default=None, blank=True, null=True)

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
    def get_add_modal_fields_json(is_admin=False):
        discord_users = sorted([u for u in User.objects.filter(social_auth__provider="discord").distinct() if u.discord_display_name], key=lambda u: (u.discord_display_name.lower(), u.discord_display_name))

        manager_options = [
            {"label": get_user_discord_username(user), "value": user.id}
            for user in discord_users
        ]

        fields = [
            {"type": "text", "label": pgettext('Dubbing name field label', 'frontend.database.models.dubbing.name'), "name": "name", "required": True},
            {"type": "textarea", "label": pgettext('Dubbing description field label', 'frontend.database.models.dubbing.description'), "name": "description"},
            {"type": "textarea", "label": pgettext('Dubbing urls field label', 'frontend.database.models.dubbing.urls'), "name": "urls"},
            {   "type": "file",
                "label": pgettext('Dubbing cover field label', 'frontend.database.models.dubbing.cover'),
                "name": "cover",
                "accept": "image/*"
            },
        ]

        if is_admin:
            fields.append(
                {
                    "type": "select",
                    "label": pgettext('Dubbing manager field label', 'frontend.database.models.dubbing.manager'),
                    "name": "manager",
                    "options": manager_options
                }
            )

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self, is_admin=False):
        discord_users = sorted([u for u in User.objects.filter(social_auth__provider="discord").distinct() if u.discord_display_name], key=lambda u: (u.discord_display_name.lower(), u.discord_display_name))

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
            {   "type": "file",
                "label": pgettext('Dubbing cover field label', 'frontend.database.models.dubbing.cover'),
                "name": "cover",
                "accept": "image/*"
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
        ]

        if is_admin:
            fields.append(
                {
                    "type": "select",
                    "label": pgettext('Dubbing manager field label', 'frontend.database.models.dubbing.manager'),
                    "name": "manager",
                    "value": self.manager.id if self.manager else None,
                    "options": manager_options,
                },
            )

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


class SceneEpisodeBase(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=128, default=f"{'%(class)s'.capitalize()} Name")
    dubbing = models.ForeignKey(Dubbing, on_delete=models.CASCADE, related_name="%(class)s")
    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(default=today)
    deadline = models.DateTimeField(default=one_week_from_now)

    script = models.FileField(max_length=512, upload_to=HashedFilePath("script", "scripts"))
    urls = models.TextField(max_length=1024, default="", blank=True)

    file_url = models.URLField(max_length=1024, default=None, blank=True, null=True)
    
    def save(self, ia=False, is_scene=False):
        if self.deadline is None or self.started > self.deadline:
            self.deadline = three_days_from(self.started) if is_scene else one_week_from(self.started)

        if self.started:
            self.started = timezone.make_aware(datetime.combine(self.started.date(), time.min), timezone.get_current_timezone())

        if self.deadline:
            self.deadline = timezone.make_aware(datetime.combine(self.deadline.date(), time.max), timezone.get_current_timezone())
        
        super().save()

    def get_video_url(self):
        if self.file_url is not None:
            return self.file_url
        return None
    
    def is_manager(self, user) -> bool:
        return self.dubbing.manager == user

class Episode(SceneEpisodeBase):
    season = models.PositiveSmallIntegerField(default=1)
    episode = models.PositiveSmallIntegerField(default=1)

    cover = models.ImageField(max_length=512, upload_to=HashedFilePath("cover", "covers/episode"), default=None, blank=True, null=True)

    def get_se(self) -> str:
        return f"S{self.season:02d}E{self.episode:02d}"

    def __str__(self):
        return f"{self.dubbing} - {self.get_se()} - {self.name}"
    
    def save(self, ia=False):
        if not ia:
            self.urls = sanitize_markdown_links(self.urls)
        
        super().save(ia=ia, is_scene=False)
    
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
    def modify_episode_data(self):
        return self.get_modify_modal_fields_json()
    
    @staticmethod
    def get_add_modal_fields_json(is_admin=False):
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
            for dubbing in Dubbing.objects.all()
        ]

        fields = [
            {"type": "text", "label": pgettext('Episode name field label', 'frontend.database.models.episode.name'), "name": "name", "required": True},
            {   "type": "file",
                "label": pgettext('Episode cover field label', 'frontend.database.models.episode.cover'),
                "name": "cover",
                "accept": "image/*"
            },
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.episode.dubbing'),
                "name": "dubbing",
                "options": dubbing_options
            },
            {"type": "date", "label": pgettext('Episode started field label', 'frontend.database.models.episode.started'), "name": "started", "value": today().strftime("%Y-%m-%d")},
            {"type": "number", "label": pgettext('Episode season field label', 'frontend.database.models.episode.season'), "name": "season", "value": 1},
            {"type": "number", "label": pgettext('Episode episode field label', 'frontend.database.models.episode.episode'), "name": "episode", "value": 1},
            {"type": "file", "label": pgettext('Episode script field label', 'frontend.database.models.episode.script'), "name": "script", "accept": ".pdf,.ass", "required": True},
            {"type": "textarea", "label": pgettext('Episode urls field label', 'frontend.database.models.episode.urls'), "name": "urls"},
            {"type": "text", "label": pgettext('Episode file url field label', 'frontend.database.models.episode.file_url'), "name": "file_url"},
        ]
        if is_admin:
            fields.insert(
                3,
                {"type": "date", "label": pgettext('Episode deadline field label', 'frontend.database.models.episode.deadline'), "name": "deadline", "value": one_week_from_now().strftime("%Y-%m-%d")}
            )

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self, is_admin=False):
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
            {   "type": "file",
                "label": pgettext('Episode cover field label', 'frontend.database.models.episode.cover'),
                "name": "cover",
                "accept": "image/*"
            },
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.episode.dubbing'),
                "name": "dubbing",
                "options": dubbing_options,
                "value": self.dubbing.id
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
                "accept": ".pdf,.ass"
            },
            {
                "type": "textarea",
                "label": pgettext('Episode urls field label', 'frontend.database.models.episode.urls'),
                "name": "urls",
                "value": self.urls or ""
            },
            {   "type": "text",
                "label": pgettext('Episode file url field label', 'frontend.database.models.episode.file_url'),
                "name": "file_url",
                "value": self.file_url or ""
            },
        ]
        if is_admin:
            fields.insert(
                2,
                {
                    "type": "date",
                    "label": pgettext('Episode started field label', 'frontend.database.models.episode.started'),
                    "name": "started",
                    "value": to_utc_iso(self.started, True, True) if self.started else ""
                }
            )
            fields.insert(
                3,
                {
                    "type": "date",
                    "label": pgettext('Episode deadline field label', 'frontend.database.models.episode.deadline'),
                    "name": "deadline",
                    "value": to_utc_iso(self.deadline, True) if self.deadline else ""
                }
            )

        return json.dumps(fields)

class Scene(SceneEpisodeBase):
    cover = models.ImageField(max_length=512, upload_to=HashedFilePath("cover", "covers/scene"), default=None, blank=True, null=True)

    def __str__(self):
        return f"{self.dubbing} - {self.name}"
    
    @property
    def times_up(self) -> bool:
        return self.deadline < timezone.now()
    
    @property
    def modify_scene_data(self):
        return self.get_modify_modal_fields_json()
    
    def save(self, ia=False):
        if not ia:
            self.urls = sanitize_markdown_links(self.urls)
        
        super().save(ia=ia, is_scene=True)
    
    def get_script_download_response(self):
        if not self.script:
            raise Http404("Script file not found")

        file_path = self.script.path
        original_ext = os.path.splitext(self.script.name)[1]
        custom_filename = f"{self.__str__()}_script{original_ext}"

        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=custom_filename)
    
    @staticmethod
    def get_add_modal_fields_json(is_admin=False):
        dubbing_options = [
            {"label": f"{dubbing}", "value": dubbing.id}
            for dubbing in Dubbing.objects.all()
        ]

        fields = [
            {"type": "text", "label": pgettext('Scene name field label', 'frontend.database.models.scene.name'), "name": "name", "required": True},
            {   "type": "file",
                "label": pgettext('Scene cover field label', 'frontend.database.models.scene.cover'),
                "name": "cover",
                "accept": "image/*"
            },
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.scene.dubbing'),
                "name": "dubbing",
                "options": dubbing_options
            },
            {"type": "date", "label": pgettext('Scene started field label', 'frontend.database.models.scene.started'), "name": "started", "value": today().strftime("%Y-%m-%d")},
            {"type": "file", "label": pgettext('Scene script field label', 'frontend.database.models.scene.script'), "name": "script", "accept": ".pdf,.ass", "required": True},
            {"type": "textarea", "label": pgettext('Scene urls field label', 'frontend.database.models.scene.urls'), "name": "urls"},
            {"type": "text", "label": pgettext('Scene file url field label', 'frontend.database.models.scene.file_url'), "name": "file_url"},
        ]
        
        if is_admin:
            fields.insert(
                3,
                {"type": "date", "label": pgettext('Scene deadline field label', 'frontend.database.models.scene.deadline'), "name": "deadline", "value": three_days_from_now().strftime("%Y-%m-%d")}
            )

        return json.dumps(fields)
    
    
    def get_modify_modal_fields_json(self, is_admin=False):
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
            {   "type": "file",
                "label": pgettext('Scene cover field label', 'frontend.database.models.scene.cover'),
                "name": "cover",
                "accept": "image/*"
            },
            {
                "type": "select",
                "label": pgettext('Dubbing field label', 'frontend.database.models.scene.dubbing'),
                "name": "dubbing",
                "options": dubbing_options,
                "value": self.dubbing.id
            },
            {
                "type": "file",
                "label": pgettext('Scene script field label', 'frontend.database.models.scene.script'),
                "name": "script",
                "accept": ".pdf,.ass"
            },
            {
                "type": "textarea",
                "label": pgettext('Scene urls field label', 'frontend.database.models.scene.urls'),
                "name": "urls",
                "value": self.urls or ""
            },
            {   "type": "text",
                "label": pgettext('Scene file url field label', 'frontend.database.models.scene.file_url'),
                "name": "file_url",
                "value": self.file_url or ""
            },
        ]
        if is_admin:
            fields.insert(
                2,
                {
                    "type": "date",
                    "label": pgettext('Episode started field label', 'frontend.database.models.episode.started'),
                    "name": "started",
                    "value": to_utc_iso(self.started, True, True) if self.started else ""
                }
            )
            fields.insert(
                3,
                {
                    "type": "date",
                    "label": pgettext('Episode deadline field label', 'frontend.database.models.episode.deadline'),
                    "name": "deadline",
                    "value": to_utc_iso(self.deadline, True) if self.deadline else ""
                }
            )

        return json.dumps(fields)



class UserCharacterBase(models.Model):
    class Meta:
        abstract = True

    episode = models.ForeignKey(Episode, on_delete=models.SET_NULL, related_name='%(class)s', null=True, blank=True)
    scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, related_name='%(class)s', null=True, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s', blank=True, null=True)
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

    def __str__(self):
        return f"{self.character} ({self.episode.dubbing if self.episode else self.scene.dubbing if self.scene else "Unknown"}) - {self.user.discord_display_name if self.user else None}"
    
    @staticmethod
    def get_add_modal_fields_json(episode:Episode=None, scene:Scene=None):
        if episode is not None:
            character_options = [
                {"label": f"{i}", "value": i.id}
                for i in Character.objects.all()
                if episode.dubbing == i.dubbing and not UserCharacterStable.objects.filter(episode=episode).filter(character=i).exists()
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
                if scene.dubbing == i.dubbing and not UserCharacterStable.objects.filter(scene=scene).filter(character=i).exists()
            ]
            scene_options = [
                {"label": f"{i}", "value": i.id}
                for i in Scene.objects.all()
                if scene == i
            ]
        discord_users = sorted([u for u in User.objects.filter(social_auth__provider="discord").distinct() if u.discord_display_name], key=lambda u: (u.discord_display_name.lower(), u.discord_display_name))
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
        discord_users = sorted([u for u in User.objects.filter(social_auth__provider="discord").distinct() if u.discord_display_name], key=lambda u: (u.discord_display_name.lower(), u.discord_display_name))
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
            "options": user_options,
            "value": self.user.id if self.user else user_options[0]["value"] if user_options and len(user_options) >= 1 else None
        })

        return json.dumps(fields)
    

class UserCharacterTemporary(UserCharacterBase):
    name = models.CharField(max_length=128, default="Character Name")
    image = models.ImageField(max_length=512, upload_to=HashedFilePath("image", "images"), default=NO_THUMBNAIL_URL, blank=True, null=True)
    description = models.TextField(max_length=1024, default="", blank=True)
    
    def save(self, ia=False):
        if not ia:
            self.description = sanitize_markdown_links(self.description)
        
        super().save()

    def __str__(self):
        return f"{self.name} ({self.episode.dubbing if self.episode else self.scene.dubbing if self.scene else "Unknown"}) - {self.user.discord_display_name if self.user else None}"
    
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
        discord_users = sorted([u for u in User.objects.filter(social_auth__provider="discord").distinct() if u.discord_display_name], key=lambda u: (u.discord_display_name.lower(), u.discord_display_name))
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
        discord_users = sorted([u for u in User.objects.filter(social_auth__provider="discord").distinct() if u.discord_display_name], key=lambda u: (u.discord_display_name.lower(), u.discord_display_name))
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
            "options": user_options,
            "value": self.user.id if self.user else user_options[0]["value"] if user_options and len(user_options) >= 1 else None
        })

        return json.dumps(fields)