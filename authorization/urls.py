from django.urls import path

from accounts.views import check_view, login_view, logout_view, register_view

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register_view, name="register"),
    path("check/", check_view, name="check"),
]
