from django.urls import path
from . import views

urlpatterns = [
    path("users/sync", views.sync_users, name="discord_sync_users"),
    path("users/add", views.add_users, name="discord_add_users"),
    path("users/remove", views.remove_users, name="discord_sync_users"),
    path("dubbings/characters", views.get_dubbings_characters, name="discord_get_dubbings_characters"),

    path("commands/announcement/<str:type>/<int:id>", views.get_announce_data, name="discord_get_announce_data"),
    path("commands/notification/<int:id>", views.user_notification, name="discord_user_notification"),
    path("commands/notification/users", views.users_notification, name="discord_users_notification"),
]
