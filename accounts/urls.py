from django.urls import path

from .views import check_view, login_view, logout_view, signup_view

app_name = "auth"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("signup/", signup_view, name="signup"),
    path("check/", check_view, name="check"),
]
