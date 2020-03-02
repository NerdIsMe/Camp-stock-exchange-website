"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from stockEx.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', login),
    path('accounts/logout/', logout),
    path('accounts/register/', register),
    path('home/', home),
    path('home/<int:stock_symbol>', stock_info),
    path('home/search_userdata/', search_userdata),
    path('home/search_userdata/<str:username>', modify_deposit),
    path('home/game_status/', gamestatus),
    path('home/game_status/reset/', gamereset),
    path('home/game_status/settings/', gamesettings),
    path('home/personal_data/', personal_data),
    path('update_stock/', update_stock),
]
