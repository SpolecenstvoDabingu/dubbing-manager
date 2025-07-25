from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('stats', views.stats, name="stats"),
    path('stats/dubbing/<int:dubbing_id>', views.stats_dubbing, name="stats_dubbing"),
    path('stats/episode/<int:episode_id>', views.stats_episode, name="stats_episode"),
    path('stats/scene/<int:scene_id>', views.stats_scene, name="stats_scene"),
    path('download-script/<str:obj_type>/<int:obj_id>/', views.download_script, name='download_script'),

    path('manage/users/', views.manage_users, name='manage_users'),
    path('manage/users/<int:id>/update', views.update_user, name='update_user'),
]
