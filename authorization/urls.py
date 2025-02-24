from django.urls import include, path

from django_prometheus.exports import ExportToDjangoView

urlpatterns = [
    path("api/auth/", include("accounts.urls", namespace="auth")),
    path("metrics", ExportToDjangoView, name="metrics"),
]
