from django.urls import path
from . import views

urlpatterns = [
    path("users/sync", views.sync_users, name="api_sync_users")
]
