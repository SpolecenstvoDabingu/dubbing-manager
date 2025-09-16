from django.urls import path, include
from . import views

urlpatterns = [
    path('dubbing/add', views.add_dubbing, name="api_add_dubbing"),
    path('dubbing/modify/<int:id>', views.modify_dubbing, name="api_modify_dubbing"),
    path('dubbing/delete/<int:id>', views.delete_dubbing, name="api_delete_dubbing"),

    path('episode/add', views.add_episode, name="api_add_episode"),
    path('episode/modify/<int:id>', views.modify_episode, name="api_modify_episode"),
    path('episode/delete/<int:id>', views.delete_episode, name="api_delete_episode"),
    path('episode/video/<int:id>', views.get_video_episode, name="api_get_video_episode"),

    path('scene/add', views.add_scene, name="api_add_scene"),
    path('scene/modify/<int:id>', views.modify_scene, name="api_modify_scene"),
    path('scene/delete/<int:id>', views.delete_scene, name="api_delete_scene"),
    path('scene/video/<int:id>', views.get_video_scene, name="api_get_video_scene"),

    path('character/add', views.add_character, name="api_add_character"),
    path('character/modify/<int:id>', views.modify_character, name="api_modify_character"),
    path('character/make_stable/<int:id>', views.character_make_stable, name="api_character_make_stable"),
    path('character/delete/<int:id>', views.delete_character, name="api_delete_character"),

    path('character/user/<str:type>/add', views.add_character_user, name="api_add_character_user"),
    path('character/user/<str:type>/modify/<int:id>', views.modify_character_user, name="api_modify_character_user"),
    path('character/user/<str:type>/delete/<int:id>', views.delete_character_user, name="api_delete_character_user"),

    path('character/<str:type>/<int:char_id>/handover/', views.hand_over, name='hand-over-character'),
    path('character/<str:type>/<int:char_id>/unhandover/', views.unhand_over, name='unhand-over-character'),
]
