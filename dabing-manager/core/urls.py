from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from discordoauth2 import views as discord_views
from django.conf.urls.static import static
from . import settings
from .utils import redirect_to_home
from django.conf.urls.i18n import set_language

urlpatterns = [
    path('', redirect_to_home),
    path('api/', include('api.urls')),
    path('discord/', include('discord.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include('social_django.urls', namespace='social')),
    path('login/', discord_views.login, name='login'),
    path('logout/', discord_views.force_logout, name='logout'),
    path('not-allowed/', discord_views.not_allowed, name='not_allowed'),
    path('i18n/setlang/', set_language, name='set_language'),
]

urlpatterns += i18n_patterns(
    path('', include('frontend.urls')),
)