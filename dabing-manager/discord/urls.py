from django.urls import path
from . import views

urlpatterns = [
    path("users/sync", views.sync_users, name="api_sync_users"),
    path("users/add", views.add_users, name="api_add_users"),
    path("users/remove", views.remove_users, name="api_sync_users"),
]
