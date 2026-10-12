from django.urls import path

from . import views

urlpatterns = [
    path("", views.game_list, name="game_list"),
    path("games/add/", views.game_add, name="game_add"),
    path("games/<int:pk>/", views.game_detail, name="game_detail"),
    path("games/<int:pk>/edit/", views.game_edit, name="game_edit"),
    path("games/<int:pk>/delete/", views.game_delete, name="game_delete"),
    path("games/<int:pk>/beat/", views.game_beat, name="game_beat"),
    path("games/<int:pk>/hundred/", views.game_hundred, name="game_hundred"),
    path("games/<int:pk>/status/", views.game_set_status, name="game_set_status"),
    path("signup/", views.signup, name="signup"),
]